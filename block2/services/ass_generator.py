"""
Block 2 — .ASS Subtitle Generator
Кинематографичный стиль субтитров: Montserrat Bold, белый, чёрная обводка, fade.
"""
from __future__ import annotations

import math
from pathlib import Path


# ── ASS Template ─────────────────────────────────────────────────────────────

SCRIPT_INFO = """\
[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709
"""

STYLES = """\
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cinema,Montserrat,54,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,2.5,1.2,2,80,80,120,1
Style: CinemaSmall,Montserrat,44,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,2.0,1.0,2,80,80,100,1
"""

EVENTS_HEADER = """\
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def _sec_to_ass(seconds: float) -> str:
    """83.456 → '0:01:23.46'"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    cs = round((s - int(s)) * 100)  # centiseconds
    return f"{h}:{m:02d}:{int(s):02d}.{cs:02d}"


def _fade_tag(fade_ms: int = 200) -> str:
    return f"{{\\fad({fade_ms},{fade_ms})}}"


def _choose_style(text: str) -> str:
    """Длинные строки — меньший шрифт."""
    return "CinemaSmall" if len(text) > 55 else "Cinema"


def generate_ass(segments: list[dict], output_path: str | Path) -> Path:
    """
    Генерирует .ass файл из сегментов.
    Ожидает поле 'text_ru' (переведённый текст) или 'text' как fallback.
    """
    output_path = Path(output_path)
    lines = [SCRIPT_INFO, STYLES, EVENTS_HEADER]

    for seg in segments:
        text = seg.get("text_ru") or seg.get("text", "")
        if not text:
            continue

        start = _sec_to_ass(seg["start"])
        end = _sec_to_ass(seg["end"])
        style = _choose_style(text)

        # Экранируем спецсимволы ASS
        text_esc = text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")
        # Перенос строки в ASS — \N
        text_esc = text_esc.replace("\n", "\\N")

        dialogue = (
            f"Dialogue: 0,{start},{end},{style},,0,0,0,,"
            f"{_fade_tag()}{text_esc}\n"
        )
        lines.append(dialogue)

    output_path.write_text("".join(lines), encoding="utf-8")
    return output_path
