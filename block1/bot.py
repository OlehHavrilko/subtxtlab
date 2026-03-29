"""Block 1 — Bot Entry Point."""
from __future__ import annotations

import asyncio
import os
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from shared.config import config
from shared.utils.logger import get_logger
from block1.handlers.idea_handler import router

logger = get_logger("block1")


async def health_handler(request: web.Request) -> web.Response:
    return web.json_response({"status": "ok", "bot": "block1"})


async def main():
    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
    dp.include_router(router)

    if config.use_webhook:
        from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

        webhook_url = f"{config.webhook_base_url}/webhook/bot1"
        await bot.set_webhook(webhook_url)
        logger.info(f"Webhook set: {webhook_url}")

        app = web.Application()
        app.router.add_get("/health", health_handler)
        SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path="/webhook/bot1")
        setup_application(app, dp, bot=bot)

        runner = web.AppRunner(app)
        await runner.setup()
        # Block 1 shares same port if same process, otherwise use different port
        port = config.health_port + 1
        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()
        logger.info(f"Block1 running on port {port}")
        await asyncio.Event().wait()
    else:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Block1 starting in polling mode")
        await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
