"""Ideas router: /api/ideas/generate, /api/ideas/plan, /api/ideas/trends"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.auth import get_telegram_user
from shared.database.supabase_client import save_idea, mark_used
from block1.services.ideas_service import generate_ideas, generate_weekly_plan, get_trends_analysis

router = APIRouter()


class IdeaRequest(BaseModel):
    theme: str
    count: int = 5


class PlanRequest(BaseModel):
    genres: str = ""


@router.post("/generate")
async def api_generate_ideas(body: IdeaRequest, user: dict = Depends(get_telegram_user)):
    ideas = await generate_ideas(body.theme, count=body.count, user_id=user.get("id", 0))
    return {"ideas": ideas}


@router.post("/plan")
async def api_weekly_plan(body: PlanRequest, user: dict = Depends(get_telegram_user)):
    ideas = await generate_weekly_plan(genres=body.genres, user_id=user.get("id", 0))
    return {"ideas": ideas}


@router.get("/trends")
async def api_trends(user: dict = Depends(get_telegram_user)):
    text = await get_trends_analysis()
    return {"analysis": text}


@router.post("/save")
async def api_save_idea(idea: dict, user: dict = Depends(get_telegram_user)):
    idea["created_by"] = user.get("id", 0)
    saved = await save_idea(idea)
    return {"saved": saved}


@router.post("/{scene_id}/use")
async def api_mark_used(scene_id: str, tiktok_url: str = "", user: dict = Depends(get_telegram_user)):
    await mark_used(scene_id, tiktok_url)
    return {"ok": True}
