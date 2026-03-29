"""
Block 1 — Groq Llama Ideas Service
Генерация контент-идей через Groq Llama-3.3-70B.
"""
from __future__ import annotations

import asyncio
import json
import re
import uuid

from groq import Groq

from shared.config import config
from shared.utils.logger import get_logger
from block1.prompts.idea_prompts import (
    IDEA_SYSTEM, TRENDS_SYSTEM,
    idea_prompt, plan_prompt, trends_prompt
)

logger = get_logger(__name__)
_groq_client: Groq | None = None


def _get_client() -> Groq:
    global _groq_client
    if _groq_client is None:
        _groq_client = Groq(api_key=config.groq_api_key)
    return _groq_client


def _extract_json_array(text: str) -> list:
    """Извлекаем JSON-массив из ответа, даже если есть markdown-обёртка."""
    # Убираем ```json ... ```
    text = re.sub(r"```(?:json)?\s*", "", text).strip("`").strip()
    start = text.find("[")
    end = text.rfind("]") + 1
    if start == -1:
        # Может быть один объект
        start = text.find("{")
        end = text.rfind("}") + 1
        if start == -1:
            return []
        return [json.loads(text[start:end])]
    return json.loads(text[start:end])


def _ensure_scene_id(idea: dict) -> dict:
    """Гарантируем уникальный scene_id."""
    sid = idea.get("scene_id", "")
    if not sid or len(sid) < 5:
        film_slug = re.sub(r"[^a-z0-9]+", "_", idea.get("film", "unknown").lower())[:20]
        idea["scene_id"] = f"{film_slug}_{uuid.uuid4().hex[:6]}"
    return idea


async def generate_ideas(theme: str, count: int = 5, user_id: int = 0) -> list[dict]:
    """Генерировать идеи сцен по теме."""
    logger.info(f"Generating {count} ideas for theme: {theme}")
    result = await asyncio.get_event_loop().run_in_executor(
        None, _generate_sync, IDEA_SYSTEM, idea_prompt(theme, count)
    )
    ideas = [_ensure_scene_id({**idea, "theme": theme, "created_by": user_id}) for idea in result]
    return ideas[:count]


async def generate_weekly_plan(genres: str = "", user_id: int = 0) -> list[dict]:
    """Генерировать контент-план на неделю (7 идей)."""
    logger.info(f"Generating weekly plan, genres: {genres!r}")
    result = await asyncio.get_event_loop().run_in_executor(
        None, _generate_sync, IDEA_SYSTEM, plan_prompt(genres)
    )
    ideas = [_ensure_scene_id({**idea, "created_by": user_id}) for idea in result]
    return ideas[:7]


async def get_trends_analysis() -> str:
    """Анализ трендов — возвращает текст, не JSON."""
    logger.info("Getting trends analysis")
    result = await asyncio.get_event_loop().run_in_executor(
        None, _trends_sync
    )
    return result


def _generate_sync(system: str, user: str) -> list[dict]:
    client = _get_client()
    response = client.chat.completions.create(
        model=config.groq_llama_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.7,
        max_tokens=8000,
    )
    raw = response.choices[0].message.content.strip()
    try:
        return _extract_json_array(raw)
    except Exception as e:
        logger.error(f"JSON parse error: {e}\nRaw: {raw[:500]}")
        return []


def _trends_sync() -> str:
    client = _get_client()
    response = client.chat.completions.create(
        model=config.groq_llama_model,
        messages=[
            {"role": "system", "content": TRENDS_SYSTEM},
            {"role": "user", "content": trends_prompt()},
        ],
        temperature=0.6,
        max_tokens=2000,
    )
    return response.choices[0].message.content.strip()
