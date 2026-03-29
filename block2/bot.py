"""
Block 2 — Bot Entry Point
Поддерживает polling (dev) и webhook (prod) автоматически.
"""
from __future__ import annotations

import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from shared.config import config
from shared.utils.logger import get_logger
from block2.handlers.video_handler import router

logger = get_logger("block2")


async def health_handler(request: web.Request) -> web.Response:
    return web.json_response({"status": "ok", "bot": "block2"})


async def main():
    os.makedirs(config.temp_dir, exist_ok=True)

    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
    dp.include_router(router)

    if config.use_webhook:
        # ── Webhook mode (Koyeb production) ───────────────────────────────────
        from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

        webhook_url = f"{config.webhook_base_url}/webhook/bot2"
        await bot.set_webhook(webhook_url)
        logger.info(f"Webhook set: {webhook_url}")

        app = web.Application()
        app.router.add_get("/health", health_handler)

        SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path="/webhook/bot2")
        setup_application(app, dp, bot=bot)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", config.health_port)
        await site.start()
        logger.info(f"Block2 running on port {config.health_port}")
        await asyncio.Event().wait()

    else:
        # ── Polling mode (local dev) ───────────────────────────────────────────
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Block2 starting in polling mode")
        await dp.start_polling(bot)


if __name__ == "__main__":
    import os
    asyncio.run(main())
