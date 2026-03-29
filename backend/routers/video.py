"""
Video router: /api/video/process
Загрузка .mp4 через браузер → обработка → Server-Sent Events прогресс → download URL.
"""
from __future__ import annotations

import asyncio
import json
import os
import shutil
import uuid
from pathlib import Path
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, StreamingResponse

from backend.auth import get_telegram_user
from shared.config import config
from shared.database.supabase_client import save_clip
from shared.utils.logger import get_logger
from block2.services.transcription import transcribe
from block2.services.translation import translate_segments
from block2.services.ass_generator import generate_ass
from block2.services.ffmpeg_processor import process_video
from block2.utils.srt_parser import parse_srt

logger = get_logger("backend.video")
router = APIRouter()

# Хранилище прогресса jobs: job_id → asyncio.Queue
_progress_queues: dict[str, asyncio.Queue] = {}
# Готовые файлы: job_id → Path
_output_files: dict[str, Path] = {}
# Владельцы задач: job_id → user_id
_job_users: dict[str, int] = {}


async def _emit(queue: asyncio.Queue, step: int, total: int, message: str, done: bool = False, error: str = ""):
    """Push SSE event to queue."""
    await queue.put({
        "step": step,
        "total": total,
        "percent": int(step / total * 100),
        "message": message,
        "done": done,
        "error": error,
    })


async def _process_job(
    job_id: str,
    video_path: Path,
    srt_path: Path | None,
    scene_id: str | None,
    user_id: int,
):
    """Фоновая задача обработки видео с прогрессом через очередь."""
    queue = _progress_queues[job_id]
    work_dir = video_path.parent
    TOTAL = 5

    try:
        # 1. Транскрипция или SRT
        if srt_path:
            await _emit(queue, 1, TOTAL, "📄 Читаю .srt субтитры...")
            segments = parse_srt(srt_path)
            subtitle_mode = "srt"
        else:
            await _emit(queue, 1, TOTAL, "🎙 Транскрибирую аудио (Whisper)...")
            segments = await transcribe(video_path)
            subtitle_mode = "auto"

        if not segments:
            await _emit(queue, 1, TOTAL, "", error="Не удалось распознать речь. Прикрепи .srt файл.")
            return

        # 2. Перевод
        await _emit(queue, 2, TOTAL, "🌐 Перевожу на русский (Llama)...")
        segments = await translate_segments(segments)

        # 3. .ass генерация
        await _emit(queue, 3, TOTAL, "✏️ Генерирую субтитры...")
        ass_path = work_dir / "subtitles.ass"
        generate_ass(segments, ass_path)

        # 4. FFmpeg
        await _emit(queue, 4, TOTAL, "🎬 Рендерю клип (9:16 + цвет + watermark)...")
        output_path = work_dir / "output.mp4"
        await process_video(video_path, ass_path, output_path)

        # 5. Готово
        _output_files[job_id] = output_path
        stat = output_path.stat()

        await save_clip({
            "scene_id": scene_id,
            "subtitle_mode": subtitle_mode,
            "output_size_bytes": stat.st_size,
            "processed_by": user_id,
        })

        await _emit(queue, 5, TOTAL, "✅ Готово!", done=True)

    except Exception as e:
        logger.exception(f"Job {job_id} failed")
        await _emit(queue, 0, TOTAL, "", error=str(e)[:300])


@router.post("/process")
async def start_processing(
    video: UploadFile = File(...),
    srt: UploadFile | None = File(None),
    scene_id: str | None = Form(None),
    user: dict = Depends(get_telegram_user),
):
    """Начать обработку видео. Возвращает job_id для SSE стрима."""
    if not (video.filename or "").lower().endswith(".mp4"):
        raise HTTPException(400, "Только .mp4 поддерживается")

    job_id = uuid.uuid4().hex[:16]
    work_dir = Path(config.temp_dir) / f"job_{job_id}"
    work_dir.mkdir(parents=True, exist_ok=True)

    # Сохраняем видео
    video_path = work_dir / "input.mp4"
    content = await video.read()
    if len(content) > config.max_video_size_bytes:
        raise HTTPException(413, f"Файл слишком большой. Максимум {config.max_video_size_mb} MB")
    video_path.write_bytes(content)

    # Сохраняем SRT если есть
    srt_path = None
    if srt and srt.filename:
        srt_path = work_dir / "input.srt"
        srt_content = await srt.read()
        srt_path.write_bytes(srt_content)

    # Создаём очередь прогресса
    queue: asyncio.Queue = asyncio.Queue()
    _progress_queues[job_id] = queue
    _job_users[job_id] = user.get("id", 0)

    # Запускаем обработку в фоне
    asyncio.create_task(
        _process_job(job_id, video_path, srt_path, scene_id, user.get("id", 0))
    )

    return {"job_id": job_id}


@router.get("/progress/{job_id}")
async def get_progress(job_id: str, user: dict = Depends(get_telegram_user)):
    """SSE стрим прогресса обработки."""
    if job_id not in _progress_queues:
        raise HTTPException(404, "Job not found")
    if _job_users.get(job_id) != user.get("id", 0):
        raise HTTPException(403, "Forbidden")

    async def event_generator() -> AsyncGenerator[str, None]:
        queue = _progress_queues[job_id]
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=60.0)
                data = json.dumps(event, ensure_ascii=False)
                yield f"data: {data}\n\n"

                if event.get("done") or event.get("error"):
                    # Чистим очередь через 10 минут
                    asyncio.create_task(_cleanup_job(job_id, delay=600))
                    break
            except asyncio.TimeoutError:
                yield "data: {\"heartbeat\": true}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/download/{job_id}")
async def download_result(job_id: str, user: dict = Depends(get_telegram_user)):
    """Скачать готовый клип."""
    output = _output_files.get(job_id)
    if not output or not output.exists():
        raise HTTPException(404, "Result not ready or expired")
    if _job_users.get(job_id) != user.get("id", 0):
        raise HTTPException(403, "Forbidden")

    return FileResponse(
        path=str(output),
        media_type="video/mp4",
        filename="cinemaclip_output.mp4",
    )


async def _cleanup_job(job_id: str, delay: int = 600):
    await asyncio.sleep(delay)
    _progress_queues.pop(job_id, None)
    _job_users.pop(job_id, None)
    output = _output_files.pop(job_id, None)
    if output and output.parent.exists():
        shutil.rmtree(output.parent, ignore_errors=True)
    logger.info(f"Cleaned up job {job_id}")
