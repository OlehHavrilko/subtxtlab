"""
CinemaClip AI — Shared Configuration
Единая точка конфигурации для обоих ботов.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


def _require(key: str) -> str:
    val = os.getenv(key)
    if not val:
        raise EnvironmentError(f"Required env var '{key}' is not set. See .env.example")
    return val


def _optional(key: str, default: str = "") -> str:
    return os.getenv(key, default)


@dataclass(frozen=True)
class Config:
    # ── Telegram ──────────────────────────────────────────────────────────────
    bot_token: str = field(default_factory=lambda: _require("BOT_TOKEN"))
    webhook_base_url: str = field(default_factory=lambda: _optional("WEBHOOK_BASE_URL"))
    mini_app_url: str = field(default_factory=lambda: _optional("MINI_APP_URL", "https://your-app.koyeb.app"))

    # ── Groq ──────────────────────────────────────────────────────────────────
    groq_api_key: str = field(default_factory=lambda: _require("GROQ_API_KEY"))
    groq_llama_model: str = field(default_factory=lambda: _optional("GROQ_LLAMA_MODEL", "llama-3.3-70b-versatile"))
    groq_whisper_model: str = field(default_factory=lambda: _optional("GROQ_WHISPER_MODEL", "whisper-large-v3"))

    # ── Supabase ──────────────────────────────────────────────────────────────
    supabase_url: str = field(default_factory=lambda: _require("SUPABASE_URL"))
    # service_role обходит RLS — только для серверного кода, никогда во фронте
    supabase_service_role_key: str = field(default_factory=lambda: _require("SUPABASE_SERVICE_ROLE_KEY"))

    # ── App ───────────────────────────────────────────────────────────────────
    log_level: str = field(default_factory=lambda: _optional("LOG_LEVEL", "INFO"))
    temp_dir: str = field(default_factory=lambda: _optional("TEMP_DIR", "/tmp/cinemaclip"))
    watermark_enabled: bool = field(default_factory=lambda: _optional("WATERMARK_ENABLED", "true").lower() == "true")
    watermark_text: str = field(default_factory=lambda: _optional("WATERMARK_TEXT", "@subtxtlab"))
    health_port: int = field(default_factory=lambda: int(_optional("HEALTH_PORT", "8080")))
    backend_port: int = field(default_factory=lambda: int(_optional("BACKEND_PORT", "8000")))
    max_video_size_mb: int = field(default_factory=lambda: int(_optional("MAX_VIDEO_SIZE_MB", "200")))

    @property
    def use_webhook(self) -> bool:
        return bool(self.webhook_base_url)

    @property
    def max_video_size_bytes(self) -> int:
        return self.max_video_size_mb * 1024 * 1024


# Singleton — импортировать везде
config = Config()
