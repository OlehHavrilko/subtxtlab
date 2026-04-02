"""Single-process entrypoint: runs FastAPI (uvicorn) + Telegram bot concurrently."""
from __future__ import annotations

import asyncio
import os

import uvicorn
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from shared.config import config
from shared.utils.logger import get_logger

logger = get_logger("run")


async def run_bot() -> None:
    from bot.bot import router
    from block2.handlers.video_handler import router as video_router

    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    dp.include_router(router)
    dp.include_router(video_router)

    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Bot started (polling)")
    await dp.start_polling(bot)


async def run_api() -> None:
    port = int(os.environ.get("PORT", config.backend_port))
    server_config = uvicorn.Config(
        "backend.main:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
    )
    server = uvicorn.Server(server_config)
    logger.info("API starting on port %d", port)
    await server.serve()


async def main() -> None:
    await asyncio.gather(run_api(), run_bot())


if __name__ == "__main__":
    asyncio.run(main())
