"""
Block 2 — FFmpeg Pipeline
9:16 кроп + burn-in субтитров (.ass) + цветокоррекция + watermark.

Smart crop: определяем центр действия через OpenCV (face/edge detection).
"""
from __future__ import annotations

import asyncio
import os
from pathlib import Path

from shared.config import config
from shared.utils.logger import get_logger

logger = get_logger(__name__)


async def get_video_info(video_path: str | Path) -> dict:
    """Получить метаданные видео через ffprobe."""
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_streams", "-show_format", str(video_path)
    ]
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
    )
    stdout, _ = await proc.communicate()

    import json
    data = json.loads(stdout.decode())
    info = {"width": 0, "height": 0, "duration": 0.0, "fps": 25.0}

    for stream in data.get("streams", []):
        if stream.get("codec_type") == "video":
            info["width"] = stream.get("width", 0)
            info["height"] = stream.get("height", 0)
            info["duration"] = float(stream.get("duration", 0) or data["format"].get("duration", 0))
            fps_raw = stream.get("r_frame_rate", "25/1")
            try:
                num, den = fps_raw.split("/")
                info["fps"] = round(float(num) / float(den), 2)
            except Exception:
                pass
            break

    return info


async def detect_crop_center(video_path: str | Path, width: int, height: int) -> int:
    """
    Определяет горизонтальный центр кропа через OpenCV.
    Берём несколько кадров, находим face/edge center.
    Fallback: центр кадра.
    """
    try:
        import cv2
        import numpy as np

        cap = cv2.VideoCapture(str(video_path))
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

        centers = []
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        sample_frames = [int(total_frames * p) for p in [0.1, 0.3, 0.5, 0.7, 0.9]]

        for frame_idx in sample_frames:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if not ret:
                continue
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            if len(faces) > 0:
                # Берём x-центр первого/главного лица
                x, _, w, _ = faces[0]
                centers.append(x + w // 2)

        cap.release()

        if centers:
            cx = int(sum(centers) / len(centers))
            logger.info(f"Smart crop center detected: x={cx}")
            return cx

    except Exception as e:
        logger.warning(f"Smart crop detection failed ({e}), using center")

    return width // 2


async def process_video(
    video_path: str | Path,
    ass_path: str | Path,
    output_path: str | Path,
) -> Path:
    """
    Полный FFmpeg pipeline:
    1. Smart crop → 9:16
    2. Scale → 1080x1920
    3. Burn .ass субтитры
    4. Цветокоррекция (medium contrast)
    5. Watermark @subtxtlab (если включён)
    6. Audio: нормализация + fade in/out
    """
    video_path = Path(video_path)
    ass_path = Path(ass_path)
    output_path = Path(output_path)

    info = await get_video_info(video_path)
    w, h = info["width"], info["height"]
    duration = info["duration"]

    logger.info(f"Processing: {w}x{h}, {duration:.1f}s")

    # ── Crop calculation ──────────────────────────────────────────────────────
    # Нужный crop: ширина = height * 9/16
    target_w = int(h * 9 / 16)
    if target_w > w:
        # Видео уже уже, чем 9:16 — крутим по высоте
        target_h = int(w * 16 / 9)
        crop_x = 0
        crop_y = max(0, (h - target_h) // 2)
        crop_filter = f"crop={w}:{target_h}:0:{crop_y}"
    else:
        cx = await detect_crop_center(video_path, w, h)
        crop_x = max(0, min(cx - target_w // 2, w - target_w))
        crop_filter = f"crop={target_w}:{h}:{crop_x}:0"

    # ── Subtitle path (escape для FFmpeg на Linux) ────────────────────────────
    ass_escaped = str(ass_path).replace("\\", "/").replace(":", "\\:")

    # ── Video filter chain ────────────────────────────────────────────────────
    vf_parts = [
        crop_filter,
        "scale=1080:1920:flags=lanczos",
        f"ass={ass_escaped}",
        "curves=preset=medium_contrast",
    ]

    if config.watermark_enabled:
        wm = config.watermark_text
        vf_parts.append(
            f"drawtext=text='{wm}':fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
            f":fontsize=28:fontcolor=white@0.6:x=w-tw-20:y=20"
            f":shadowcolor=black@0.4:shadowx=1:shadowy=1"
        )

    vf = ",".join(vf_parts)

    # ── Audio: нормализация громкости + fade ──────────────────────────────────
    fade_out_start = max(0, duration - 1.0)
    af = f"loudnorm,afade=t=in:d=0.3,afade=t=out:st={fade_out_start:.2f}:d=1.0"

    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-vf", vf,
        "-af", af,
        "-c:v", "libx264", "-crf", "20", "-preset", "fast",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        str(output_path),
    ]

    logger.info(f"FFmpeg command: {' '.join(cmd)}")

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()

    if proc.returncode != 0:
        err = stderr.decode()[-1000:]
        raise RuntimeError(f"FFmpeg failed:\n{err}")

    logger.info(f"Output: {output_path} ({output_path.stat().st_size // 1024} KB)")
    return output_path
