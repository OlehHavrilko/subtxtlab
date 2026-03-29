"""
Block 2 — Video Handler
Приём .mp4 от пользователя → обработка → отправка готового клипа.
"""
from __future__ import annotations

import asyncio
import os
import tempfile
import uuid
from pathlib import Path

from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, Document

from shared.config import config
from shared.database.supabase_client import get_idea, save_clip
from shared.utils.logger import get_logger
from block2.services.transcription import transcribe
from block2.services.translation import translate_segments
from block2.services.ass_generator import generate_ass
from block2.services.ffmpeg_processor import process_video
from block2.utils.srt_parser import parse_srt

logger = get_logger(__name__)
router = Router()


# ── /start ────────────────────────────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(msg: Message):
    await msg.answer(
        "🎬 <b>CinemaClip AI — Video Processor</b>\n\n"
        f"Отправь мне <b>.mp4</b> файл (до {config.max_video_size_mb}MB) — получишь клип 9:16 с русскими субтитрами.\n\n"
        "<b>Опционально:</b>\n"
        "• Прикрепи <b>.srt</b> файл вместо автотранскрипции\n"
        "• Добавь <b>scene_id</b> в подпись — подтянутся описание и хэштеги из Block 1\n\n"
        "📌 <i>Пример подписи:</i> <code>br2049_royspeech_001</code>",
        parse_mode="HTML"
    )


@router.message(Command("help"))
async def cmd_help(msg: Message):
    await msg.answer(
        "📖 <b>Как использовать:</b>\n\n"
        "1️⃣ Отправь <b>.mp4</b> (можно с подписью scene_id)\n"
        "2️⃣ Опционально: сначала отправь <b>.srt</b> файл\n"
        "3️⃣ Получи готовый клип <b>9:16</b> с 🇷🇺 субтитрами\n\n"
        f"⚠️ Максимальный размер: {config.max_video_size_mb} MB",
        parse_mode="HTML"
    )


# ── SRT buffer (per user, 5 min TTL) ─────────────────────────────────────────
_srt_buffer: dict[int, tuple[Path, float]] = {}
_SRT_TTL = 300  # секунд


@router.message(F.document & F.document.mime_type.in_({"text/plain", "application/x-subrip"}))
async def receive_srt(msg: Message):
    """Принять .srt файл — сохранить временно."""
    doc: Document = msg.document
    if not doc.file_name.endswith(".srt"):
        return

    tmp = Path(config.temp_dir) / f"srt_{msg.from_user.id}_{uuid.uuid4().hex[:8]}.srt"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    await msg.bot.download(doc, destination=tmp)

    import time
    _srt_buffer[msg.from_user.id] = (tmp, time.time())
    await msg.answer("✅ <b>.srt получен</b>. Теперь отправь .mp4 — субтитры уже готовы.", parse_mode="HTML")


# ── Main: .mp4 processing ─────────────────────────────────────────────────────

@router.message(F.video | (F.document & F.document.file_name.regexp(r"\.mp4$")))
async def receive_video(msg: Message):
    """Основной хендлер: принимаем .mp4 → обрабатываем."""
    import time

    user_id = msg.from_user.id
    scene_id = (msg.caption or "").strip() or None

    # ── Определяем файл ───────────────────────────────────────────────────────
    if msg.video:
        file_obj = msg.video
        file_size = msg.video.file_size
    else:
        file_obj = msg.document
        file_size = msg.document.file_size

    if file_size and file_size > config.max_video_size_bytes:
        await msg.answer(
            f"❌ Файл слишком большой ({file_size // 1024 // 1024} MB). "
            f"Максимум: {config.max_video_size_mb} MB"
        )
        return

    # ── Рабочая директория ────────────────────────────────────────────────────
    work_dir = Path(config.temp_dir) / f"job_{uuid.uuid4().hex[:12]}"
    work_dir.mkdir(parents=True, exist_ok=True)

    status_msg = await msg.answer("⏳ <b>Загружаю видео...</b>", parse_mode="HTML")

    try:
        # 1. Скачиваем видео
        video_path = work_dir / "input.mp4"
        await msg.bot.download(file_obj, destination=video_path)

        # 2. Определяем источник субтитров
        srt_data = _srt_buffer.pop(user_id, None)
        if srt_data:
            srt_path, ts = srt_data
            if time.time() - ts < _SRT_TTL:
                await status_msg.edit_text("📄 <b>Читаю .srt субтитры...</b>", parse_mode="HTML")
                segments = parse_srt(srt_path)
                subtitle_mode = "srt"
                srt_path.unlink(missing_ok=True)
            else:
                srt_path.unlink(missing_ok=True)
                segments = None
                subtitle_mode = "auto"
        else:
            segments = None
            subtitle_mode = "auto"

        # 3. Транскрипция (если нет .srt)
        if segments is None:
            await status_msg.edit_text("🎙 <b>Транскрибирую аудио (Whisper)...</b>", parse_mode="HTML")
            segments = await transcribe(video_path)

        if not segments:
            await status_msg.edit_text("❌ Не удалось распознать речь в видео. Попробуй прикрепить .srt файл.")
            return

        # 4. Перевод EN→RU
        await status_msg.edit_text("🌐 <b>Перевожу на русский (Llama)...</b>", parse_mode="HTML")
        segments = await translate_segments(segments)

        # 5. Генерация .ass
        await status_msg.edit_text("✏️ <b>Генерирую субтитры...</b>", parse_mode="HTML")
        ass_path = work_dir / "subtitles.ass"
        generate_ass(segments, ass_path)

        # 6. FFmpeg pipeline
        await status_msg.edit_text("🎬 <b>Рендерю клип (9:16 + субтитры + цвет)...</b>", parse_mode="HTML")
        output_path = work_dir / "output.mp4"
        await process_video(video_path, ass_path, output_path)

        # 7. Подтягиваем описание из Block 1 если есть scene_id
        caption_parts = ["✅ <b>Готово!</b>"]
        if scene_id:
            idea = await get_idea(scene_id)
            if idea:
                caption_parts.append(
                    f"\n🎥 <b>{idea['film']}</b> ({idea.get('year', '')})\n"
                    f"⏱ {idea.get('timecode_start', '')} — {idea.get('timecode_end', '')}\n\n"
                    f"📝 {idea.get('description', '')}\n\n"
                    f"🎚️ {idea.get('hashtags', '')}"
                )

        await status_msg.edit_text("\n".join(caption_parts), parse_mode="HTML")

        # 8. Отправляем видео
        await msg.answer_video(
            video=open(output_path, "rb"),
            caption="\n".join(caption_parts),
            parse_mode="HTML",
        )

        # 9. Логируем в Supabase
        stat = output_path.stat()
        await save_clip({
            "scene_id": scene_id,
            "original_filename": getattr(file_obj, "file_name", "video.mp4"),
            "duration_sec": None,
            "subtitle_mode": subtitle_mode,
            "output_size_bytes": stat.st_size,
            "processed_by": user_id,
        })

        await status_msg.delete()

    except Exception as e:
        logger.exception(f"Processing failed for user {user_id}")
        await status_msg.edit_text(f"❌ <b>Ошибка при обработке:</b>\n<code>{str(e)[:300]}</code>", parse_mode="HTML")
    finally:
        # Чистим временные файлы
        import shutil
        shutil.rmtree(work_dir, ignore_errors=True)
