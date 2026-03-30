"""Supabase client — shared between both bots."""
from __future__ import annotations

from supabase import create_client, Client
from shared.config import config
from shared.utils.logger import get_logger

logger = get_logger(__name__)

_client: Client | None = None


def get_supabase() -> Client:
    global _client
    if _client is None:
        _client = create_client(config.supabase_url, config.supabase_service_role_key)
        logger.info("Supabase client initialized")
    return _client


# ── Ideas ─────────────────────────────────────────────────────────────────────

async def save_idea(data: dict) -> dict:
    """Сохранить идею сцены в Supabase."""
    sb = get_supabase()
    result = sb.table("ideas").upsert(data).execute()
    return result.data[0] if result.data else {}


async def get_idea(scene_id: str) -> dict | None:
    """Получить идею по scene_id."""
    sb = get_supabase()
    result = sb.table("ideas").select("*").eq("scene_id", scene_id).execute()
    return result.data[0] if result.data else None


async def list_ideas(user_id: int, limit: int = 10) -> list[dict]:
    """Список сохранённых идей пользователя."""
    sb = get_supabase()
    result = (
        sb.table("ideas")
        .select("*")
        .eq("created_by", user_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return result.data or []


async def mark_used(scene_id: str, tiktok_url: str = "") -> None:
    """Пометить сцену как опубликованную."""
    sb = get_supabase()
    sb.table("used_scenes").upsert({"scene_id": scene_id, "tiktok_url": tiktok_url}).execute()


async def get_used_scene_ids(user_id: int) -> set[str]:
    """Множество уже использованных scene_id для дедупликации."""
    sb = get_supabase()
    ideas = sb.table("ideas").select("scene_id").eq("created_by", user_id).execute()
    if not ideas.data:
        return set()
    ids = [r["scene_id"] for r in ideas.data]
    used = sb.table("used_scenes").select("scene_id").in_("scene_id", ids).execute()
    return {r["scene_id"] for r in (used.data or [])}


# ── Processed clips ───────────────────────────────────────────────────────────

async def save_clip(data: dict) -> dict:
    sb = get_supabase()
    result = sb.table("processed_clips").insert(data).execute()
    return result.data[0] if result.data else {}
