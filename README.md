# CinemaClip AI 🎬

Единый Telegram-бот + Telegram Mini App для @subtxtlab.

Всё сделано с упором на бесплатный стек.

## Что умеет

- 🔍 Генерация идей сцен по теме
- 📅 Недельный контент-план
- 📈 Анализ трендов ниши
- 🎬 Обработка `.mp4` в `9:16` с RU-субтитрами
- 💾 Архив сцен в Supabase

## Бесплатный стек

| Компонент | Технология | Free Tier |
|---|---|---|
| Bot + Mini App backend | Python + FastAPI + aiogram | open source |
| Транскрипция | Groq Whisper large-v3 | бесплатные лимиты Groq |
| Генерация / перевод | Groq Llama-3.3-70B | бесплатные лимиты Groq |
| Видео | FFmpeg + libass | open source |
| База | Supabase PostgreSQL | free plan |
| Хостинг | Koyeb | free tier |

## Структура

```text
backend/        # FastAPI API (ideas/video/scenes)
frontend/       # React Mini App
bot/            # единый Telegram бот (/start + fallback video processing)
shared/         # config, logger, supabase client, migrations
block1/         # сервисы генерации идей
block2/         # сервисы видеообработки
```

## Локальный запуск

```bash
cp .env.example .env
# заполни переменные

# 1) миграция в Supabase
# shared/database/migrations/001_initial.sql

# 2) frontend
cd frontend
npm install
npm run build
cd ..

# 3) backend
uvicorn backend.main:app --host 0.0.0.0 --port 8000

# 4) bot (в отдельном терминале)
python -m bot.bot
```

## Docker compose

```bash
docker compose up --build
```

Сервисы:
- `backend` — API и раздача `frontend/dist`
- `bot` — Telegram bot

## Koyeb (бесплатно)

Создай 2 сервиса из одного репозитория, оба используют один `Dockerfile`.

### Сервис 1: `backend`
- **Build**: Docker (автоматически соберёт frontend внутри образа)
- **Run command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
- **Port**: `8000` (или оставь пустым — Koyeb сам назначит через `$PORT`)

### Сервис 2: `bot`
- **Build**: тот же Docker-образ
- **Run command**: `python -m bot.bot`
- **Port**: не нужен (polling, нет HTTP-сервера)

### Переменные окружения (оба сервиса)

| Переменная | Описание |
|---|---|
| `BOT_TOKEN` | Токен бота от @BotFather |
| `GROQ_API_KEY` | Ключ Groq API |
| `SUPABASE_URL` | URL проекта Supabase |
| `SUPABASE_SERVICE_ROLE_KEY` | service_role ключ Supabase |
| `MINI_APP_URL` | **URL backend-сервиса на Koyeb** (туда открывается Mini App) |
| `WEBHOOK_BASE_URL` | Оставь пустым — используется polling |

## Obsidian sync

```bash
./scripts/sync_obsidian_notes.sh
```

Опционально можно указать путь к vault:

```bash
./scripts/sync_obsidian_notes.sh /path/to/ObsidianVault
```
