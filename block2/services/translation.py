"""
Block 2 — Translation Service
Groq Llama-3.3-70B: переводит субтитры EN→RU с сохранением тайминга.
Работает батчами, чтобы не превышать лимит токенов.
"""
from __future__ import annotations

import asyncio
import json

from groq import Groq

from shared.config import config
from shared.utils.logger import get_logger

logger = get_logger(__name__)

_groq_client: Groq | None = None

BATCH_SIZE = 40  # сегментов за один запрос

SYSTEM_PROMPT = """You are a professional film subtitle translator (English → Russian).
Rules:
- Return ONLY a JSON array of translated strings, same order, same count as input.
- Translate naturally, preserve tone of voice — NOT word-for-word.
- Do NOT translate character names, film titles, brand names.
- For philosophical quotes — convey meaning, not literal words.
- Short lines (≤3 words) — keep as is or minimal change.
- Never merge or split subtitle lines.
- Output: ["translated line 1", "translated line 2", ...]"""


def _get_client() -> Groq:
    global _groq_client
    if _groq_client is None:
        _groq_client = Groq(api_key=config.groq_api_key)
    return _groq_client


async def translate_segments(segments: list[dict]) -> list[dict]:
    """
    Переводит список сегментов. Возвращает сегменты с полем 'text_ru'.
    """
    if not segments:
        return segments

    logger.info(f"Translating {len(segments)} segments")

    # Разбиваем на батчи
    batches = [segments[i:i + BATCH_SIZE] for i in range(0, len(segments), BATCH_SIZE)]
    results = []

    for batch in batches:
        translated = await asyncio.get_event_loop().run_in_executor(
            None, _translate_batch_sync, [s["text"] for s in batch]
        )
        for seg, ru_text in zip(batch, translated):
            results.append({**seg, "text_ru": ru_text})

    logger.info("Translation complete")
    return results


def _translate_batch_sync(texts: list[str]) -> list[str]:
    client = _get_client()
    user_msg = json.dumps(texts, ensure_ascii=False)

    response = client.chat.completions.create(
        model=config.groq_llama_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.3,
        max_tokens=4096,
    )

    raw = response.choices[0].message.content.strip()

    # Вырезаем JSON-массив, даже если модель добавила markdown
    start = raw.find("[")
    end = raw.rfind("]") + 1
    if start == -1 or end == 0:
        logger.warning("Groq returned unexpected format, falling back to originals")
        return texts

    try:
        translated: list[str] = json.loads(raw[start:end])
    except json.JSONDecodeError:
        logger.warning("JSON decode error in translation, falling back to originals")
        return texts

    # Если модель вернула меньше строк — дополняем оригиналами
    if len(translated) < len(texts):
        translated += texts[len(translated):]

    return translated[:len(texts)]
