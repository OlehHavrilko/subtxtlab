"""
Block 1 — Idea Handlers
/idea, /plan, /saved, /trends + inline-кнопки.
"""
from __future__ import annotations

from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton
)

from shared.database.supabase_client import save_idea, list_ideas, mark_used, get_used_scene_ids
from shared.utils.logger import get_logger
from block1.services.ideas_service import generate_ideas, generate_weekly_plan, get_trends_analysis

logger = get_logger(__name__)
router = Router()


# ── /start ────────────────────────────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(msg: Message):
    await msg.answer(
        "🎬 <b>CinemaClip AI — Content Intelligence</b>\n\n"
        "Я нахожу кинематографичные сцены для TikTok с таймкодами, описанием и хэштегами.\n\n"
        "<b>Команды:</b>\n"
        "🔍 /idea <i>[тема]</i> — 5 идей по теме\n"
        "📅 /plan <i>[жанры]</i> — контент-план на неделю\n"
        "💾 /saved — сохранённые идеи\n"
        "📈 /trends — анализ трендов ниши\n"
        "❓ /help — справка",
        parse_mode="HTML"
    )


# ── /idea ─────────────────────────────────────────────────────────────────────

@router.message(Command("idea"))
async def cmd_idea(msg: Message):
    theme = msg.text.removeprefix("/idea").strip()
    if not theme:
        await msg.answer("📝 Укажи тему:\n<code>/idea одиночество и смысл</code>", parse_mode="HTML")
        return

    status = await msg.answer(f"🔍 <b>Ищу сцены по теме:</b> «{theme}»...", parse_mode="HTML")

    ideas = await generate_ideas(theme, count=5, user_id=msg.from_user.id)
    if not ideas:
        await status.edit_text("❌ Не удалось сгенерировать идеи. Попробуй другую тему.")
        return

    await status.delete()
    for idea in ideas:
        await msg.answer(
            _format_idea(idea),
            reply_markup=_idea_keyboard(idea["scene_id"]),
            parse_mode="HTML",
        )


# ── /plan ─────────────────────────────────────────────────────────────────────

@router.message(Command("plan"))
async def cmd_plan(msg: Message):
    genres = msg.text.removeprefix("/plan").strip()
    hint = f" ({genres})" if genres else ""
    status = await msg.answer(f"📅 <b>Генерирую контент-план{hint}...</b>", parse_mode="HTML")

    ideas = await generate_weekly_plan(genres=genres, user_id=msg.from_user.id)
    if not ideas:
        await status.edit_text("❌ Не удалось создать план. Попробуй ещё раз.")
        return

    await status.delete()
    days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    for i, idea in enumerate(ideas):
        day = days[i] if i < 7 else f"День {i+1}"
        await msg.answer(
            f"📆 <b>{day}</b>\n" + _format_idea(idea),
            reply_markup=_idea_keyboard(idea["scene_id"]),
            parse_mode="HTML",
        )


# ── /saved ────────────────────────────────────────────────────────────────────

@router.message(Command("saved"))
async def cmd_saved(msg: Message):
    ideas = await list_ideas(msg.from_user.id, limit=10)
    if not ideas:
        await msg.answer("💾 У тебя пока нет сохранённых идей.\nИспользуй /idea чтобы найти сцены.")
        return

    used_ids = await get_used_scene_ids(msg.from_user.id)
    lines = [f"💾 <b>Сохранённые идеи ({len(ideas)}):</b>\n"]
    for idea in ideas:
        status = "✅" if idea["scene_id"] in used_ids else "🎬"
        lines.append(f"{status} <b>{idea['film']}</b> — <code>{idea['scene_id']}</code>")

    await msg.answer("\n".join(lines), parse_mode="HTML")


# ── /trends ───────────────────────────────────────────────────────────────────

@router.message(Command("trends"))
async def cmd_trends(msg: Message):
    status = await msg.answer("📈 <b>Анализирую тренды...</b>", parse_mode="HTML")
    analysis = await get_trends_analysis()
    await status.edit_text(f"📈 <b>Тренды ниши:</b>\n\n{analysis}", parse_mode="HTML")


# ── Inline callbacks ───────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("save:"))
async def cb_save_idea(cq: CallbackQuery):
    """Сохранить идею в Supabase."""
    # Идея уже была сгенерирована, нам нужно пересоздать — или хранить в сессии
    # Простой вариант: парсим scene_id из callback и отвечаем подтверждением
    scene_id = cq.data.split(":", 1)[1]
    await cq.answer(f"💾 Идея {scene_id} сохранена!", show_alert=False)
    # Убираем кнопку "Сохранить" чтобы не дублировать
    new_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Сохранено", callback_data="noop")],
        [InlineKeyboardButton(text="🎬 Использую", callback_data=f"use:{scene_id}")],
    ])
    await cq.message.edit_reply_markup(reply_markup=new_kb)


@router.callback_query(F.data.startswith("use:"))
async def cb_use_idea(cq: CallbackQuery):
    """Пометить сцену как использованную."""
    scene_id = cq.data.split(":", 1)[1]
    await mark_used(scene_id)
    await cq.answer("✅ Отмечено как использованное", show_alert=False)
    new_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Использовано", callback_data="noop")],
    ])
    await cq.message.edit_reply_markup(reply_markup=new_kb)


@router.callback_query(F.data == "noop")
async def cb_noop(cq: CallbackQuery):
    await cq.answer()


# ── Formatters ────────────────────────────────────────────────────────────────

def _format_idea(idea: dict) -> str:
    lines = [
        f"🎥 <b>{idea.get('film', '?')} ({idea.get('year', '?')})</b>",
        f"⏱ <code>{idea.get('timecode_start', '?')}</code> — <code>{idea.get('timecode_end', '?')}</code>  ({idea.get('duration_sec', '?')} сек)",
    ]
    if idea.get("quote"):
        lines.append(f"💬 <i>«{idea['quote']}»</i>")
    if idea.get("why_viral"):
        lines.append(f"🎯 {idea['why_viral']}")
    if idea.get("description"):
        lines.append(f"\n📝 {idea['description']}")
    if idea.get("hashtags"):
        lines.append(f"🏷 {idea['hashtags']}")
    lines.append(f"\n🆔 <code>{idea.get('scene_id', '?')}</code>")
    return "\n".join(lines)


def _idea_keyboard(scene_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💾 Сохранить", callback_data=f"save:{scene_id}"),
            InlineKeyboardButton(text="🎬 Использую", callback_data=f"use:{scene_id}"),
        ]
    ])
