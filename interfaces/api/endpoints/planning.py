from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from planning.planner import create_plan, record_review, get_due_tasks
from planning.monitor import get_plan_progress, get_review_stats

router = APIRouter()


class CreatePlanRequest(BaseModel):
    title: str
    goal: str
    description: str = ""
    priority: int = 5
    daily_hours: float = 1.0


class ReviewRequest(BaseModel):
    task_id: int
    score: float          # 0.0 - 1.0
    knowledge_item_id: int | None = None


@router.post("/plans")
async def create_learning_plan(req: CreatePlanRequest, db: AsyncSession = Depends(get_db)):
    plan = await create_plan(
        db,
        title=req.title,
        goal=req.goal,
        description=req.description,
        priority=req.priority,
        daily_hours=req.daily_hours,
    )
    return {"plan_id": plan.id, "title": plan.title, "estimated_hours": plan.estimated_hours}


@router.get("/plans/{plan_id}/progress")
async def plan_progress(plan_id: int, db: AsyncSession = Depends(get_db)):
    return await get_plan_progress(db, plan_id)


@router.get("/tasks/due")
async def due_tasks(db: AsyncSession = Depends(get_db)):
    tasks = await get_due_tasks(db)
    return {
        "tasks": [
            {"id": t.id, "title": t.title, "plan_id": t.plan_id,
             "estimated_minutes": t.estimated_minutes, "status": t.status}
            for t in tasks
        ]
    }


@router.post("/reviews")
async def submit_review(req: ReviewRequest, db: AsyncSession = Depends(get_db)):
    record = await record_review(db, req.task_id, req.score, req.knowledge_item_id)
    return {
        "review_id": record.id,
        "next_review_at": record.next_review_at.isoformat(),
        "interval_days": record.interval_days,
        "ease_factor": record.ease_factor,
    }


@router.get("/stats")
async def review_stats(days: int = 30, db: AsyncSession = Depends(get_db)):
    return await get_review_stats(db, days=days)
