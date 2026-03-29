"""
CinemaClip AI — Единый Telegram Бот
Открывает Mini App + принимает .mp4 напрямую как fallback.
"""
from __future__ import annotations

import asyncio
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart
from aiogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
)
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from shared.config import config
from shared.utils.logger import get_logger
from block2.handlers.video_handler import router as video_router

logger = get_logger("bot")
router = Router()


def app_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="🎬 Открыть CinemaClip AI",
            web_app=WebAppInfo(url=config.mini_app_url)
        )
    ]])


@router.message(CommandStart())
async def cmd_start(msg: Message):
    name = msg.from_user.first_name
    await msg.answer(
        f"Привет, <b>{name}</b>! 👋\n\n"
        "🎬 <b>CinemaClip AI</b> — система автоматизации TikTok-контента для @subtxtlab\n\n"
        "Открой приложение:\n"
        "• 🔍 Поиск кинематографичных сцен по теме\n"
        "• 📅 Контент-план на неделю\n"
        "• 📈 Анализ трендов ниши\n"
        "• 🎬 Обработка .mp4 → 9:16 с русскими субтитрами\n"
        "• 💾 Архив сохранённых идей",
        reply_markup=app_keyboard(),
        parse_mode=ParseMode.HTML,
    )


@router.message(F.text.startswith("/app"))
async def cmd_app(msg: Message):
    await msg.answer("Открывай 👇", reply_markup=app_keyboard())


async def main():
    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
    dp.include_router(router)
    dp.include_router(video_router)  # Fallback: принимает .mp4 напрямую в бот

    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Bot started (polling mode)")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
