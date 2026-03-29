"""
Block 2 — Transcription Service
Groq Whisper large-v3: аудио → SRT субтитры с таймингами.
Возвращает список сегментов {start, end, text}.
"""
from __future__ import annotations

import asyncio
import os
import tempfile
from pathlib import Path

from groq import Groq

from shared.config import config
from shared.utils.logger import get_logger

logger = get_logger(__name__)

_groq_client: Groq | None = None


def _get_client() -> Groq:
    global _groq_client
    if _groq_client is None:
        _groq_client = Groq(api_key=config.groq_api_key)
    return _groq_client


async def transcribe(video_path: str | Path) -> list[dict]:
    """
    Транскрибировать аудио из видео через Groq Whisper.
    Возвращает список: [{"index": 1, "start": 0.0, "end": 2.5, "text": "..."}]
    """
    video_path = Path(video_path)
    logger.info(f"Transcribing: {video_path.name}")

    # Извлекаем аудио в WAV (16kHz mono — оптимально для Whisper)
    audio_path = video_path.with_suffix(".wav")
    extract_cmd = [
        "ffmpeg", "-y", "-i", str(video_path),
        "-ar", "16000", "-ac", "1",
        "-vn", str(audio_path)
    ]
    proc = await asyncio.create_subprocess_exec(
        *extract_cmd,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    await proc.wait()

    if not audio_path.exists():
        raise RuntimeError("FFmpeg failed to extract audio")

    try:
        segments = await asyncio.get_event_loop().run_in_executor(
            None, _transcribe_sync, str(audio_path)
        )
    finally:
        audio_path.unlink(missing_ok=True)

    logger.info(f"Transcription done: {len(segments)} segments")
    return segments


def _transcribe_sync(audio_path: str) -> list[dict]:
    client = _get_client()
    with open(audio_path, "rb") as f:
        response = client.audio.transcriptions.create(
            model=config.groq_whisper_model,
            file=f,
            response_format="verbose_json",
            timestamp_granularities=["segment"],
            language="en",
        )

    segments = []
    for i, seg in enumerate(response.segments or [], start=1):
        segments.append({
            "index": i,
            "start": float(seg.get("start", 0)),
            "end": float(seg.get("end", 0)),
            "text": seg.get("text", "").strip(),
        })
    return segments
