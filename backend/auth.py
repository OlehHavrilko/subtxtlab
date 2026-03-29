"""Telegram Mini App auth helpers."""
from __future__ import annotations

import hashlib
import hmac
import json
from urllib.parse import parse_qsl

from fastapi import HTTPException, Request

from shared.config import config


def validate_telegram_init_data(init_data: str, bot_token: str) -> dict | None:
    """Validate Telegram WebApp initData and return parsed user."""
    try:
        parsed = dict(parse_qsl(init_data, strict_parsing=True))
        received_hash = parsed.pop("hash", None)
        if not received_hash:
            return None

        data_check = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
        secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
        expected_hash = hmac.new(secret_key, data_check.encode(), hashlib.sha256).hexdigest()

        if not hmac.compare_digest(expected_hash, received_hash):
            return None

        return json.loads(parsed.get("user", "{}"))
    except Exception:
        return None


async def get_telegram_user(request: Request) -> dict:
    """FastAPI dependency: extract & validate Telegram user from header."""
    init_data = request.headers.get("X-Telegram-Init-Data", "") or request.query_params.get("init_data", "")

    # Dev mode: allow local calls without Telegram wrapper
    if not init_data and not config.use_webhook:
        return {"id": 0, "first_name": "DevUser"}

    user = validate_telegram_init_data(init_data, config.bot_token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid Telegram auth")
    return user
