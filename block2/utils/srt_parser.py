"""
Block 2 — SRT Parser
Парсит .srt файл → тот же формат сегментов, что и transcription.py
"""
from __future__ import annotations

import re
from pathlib import Path


def parse_srt(srt_path: str | Path) -> list[dict]:
    """
    Парсит .srt файл.
    Возвращает: [{"index": 1, "start": 0.0, "end": 2.5, "text": "..."}]
    """
    text = Path(srt_path).read_text(encoding="utf-8", errors="replace")
    segments = []

    # Паттерн: индекс, таймкод, текст
    pattern = re.compile(
        r"(\d+)\s*\n"
        r"(\d{2}:\d{2}:\d{2}[,\.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,\.]\d{3})\s*\n"
        r"([\s\S]*?)(?=\n\d+\s*\n|\Z)",
        re.MULTILINE,
    )

    for match in pattern.finditer(text):
        idx = int(match.group(1))
        start = _tc_to_sec(match.group(2))
        end = _tc_to_sec(match.group(3))
        content = match.group(4).strip()
        # Убираем HTML теги (<i>, <b> и т.д.)
        content = re.sub(r"<[^>]+>", "", content)
        if content:
            segments.append({"index": idx, "start": start, "end": end, "text": content})

    return segments


def _tc_to_sec(tc: str) -> float:
    """'00:01:23,456' → 83.456"""
    tc = tc.replace(",", ".")
    parts = tc.split(":")
    h, m, s = int(parts[0]), int(parts[1]), float(parts[2])
    return h * 3600 + m * 60 + s
