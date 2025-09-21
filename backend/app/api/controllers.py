from fastapi import APIRouter, HTTPException
from typing import List
from app.infra.sql_repository import SqlAccountRepository, ensure_tables
from app.application.use_cases import ListFlaggedUseCase
from app.api.schemas import FlaggedOut

router = APIRouter(prefix="/api")

@router.on_event("startup")
async def ensure_db():
    await ensure_tables()

@router.get("/flags", response_model=List[FlaggedOut])
async def list_flags(limit: int = 100):
    repo = SqlAccountRepository()
    usecase = ListFlaggedUseCase(repo)
    rows = await usecase.execute(limit=limit)
    return rows

@router.post("/report/{platform}/{handle}")
async def mark_for_review(platform: str, handle: str):
    repo = SqlAccountRepository()
    f = await repo.find_by_handle(platform, handle)
    if not f:
        raise HTTPException(status_code=404, detail="Not found")
    return {"status": "marked_for_manual_review", "platform": platform, "handle": handle}
