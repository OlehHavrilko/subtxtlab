# Koyeb: два сервиса (PORT инжектится автоматически)
backend: uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-${BACKEND_PORT:-8000}}
bot: python -m bot.bot
