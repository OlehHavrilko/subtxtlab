# ── Stage 1: Build React frontend ────────────────────────────────────────────
FROM node:20-slim AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# ── Stage 2: Python backend ───────────────────────────────────────────────────
FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    libopencv-dev \
    fonts-open-sans \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
# Inject built frontend (served as static by FastAPI)
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Koyeb injects $PORT; docker-compose uses $BACKEND_PORT; fallback 8000
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-${BACKEND_PORT:-8000}}"]
