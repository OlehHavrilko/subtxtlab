"""Scenes router: /api/scenes — saved ideas from Supabase"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from backend.auth import get_telegram_user
from shared.database.supabase_client import list_ideas, get_idea, get_used_scene_ids

router = APIRouter()


@router.get("/")
async def api_list_scenes(user: dict = Depends(get_telegram_user)):
    ideas = await list_ideas(user.get("id", 0), limit=50)
    used = await get_used_scene_ids(user.get("id", 0))
    for idea in ideas:
        idea["used"] = idea["scene_id"] in used
    return {"scenes": ideas}


@router.get("/{scene_id}")
async def api_get_scene(scene_id: str, user: dict = Depends(get_telegram_user)):
    idea = await get_idea(scene_id)
    if not idea:
        from fastapi import HTTPException
        raise HTTPException(404, "Scene not found")
    return idea
