"""CinemaClip AI — FastAPI Backend."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.routers import ideas, video, scenes
from shared.utils.logger import get_logger

logger = get_logger("backend")

app = FastAPI(title="CinemaClip AI API", version="1.0.0")

# ── CORS (Telegram Mini App открывается с telegram.org и нашего домена) ────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ideas.router, prefix="/api/ideas", tags=["ideas"])
app.include_router(video.router, prefix="/api/video", tags=["video"])
app.include_router(scenes.router, prefix="/api/scenes", tags=["scenes"])


@app.get("/health")
async def health():
    return {"status": "ok", "service": "cinemaclip-backend"}


# ── Serve frontend in production ──────────────────────────────────────────────
frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="static")

