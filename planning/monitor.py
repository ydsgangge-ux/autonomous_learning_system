"""Monitor learning progress and generate statistics."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from db.models import LearningPlan, LearningTask, ReviewRecord, TaskStatus
from core.utils import get_logger

logger = get_logger(__name__)


async def get_plan_progress(session: AsyncSession, plan_id: int) -> dict:
    """Return progress stats for a learning plan."""
    plan = await session.get(LearningPlan, plan_id)
    if not plan:
        return {}

    total = (await session.execute(
        select(func.count()).select_from(LearningTask).where(LearningTask.plan_id == plan_id)
    )).scalar_one()

    completed = (await session.execute(
        select(func.count()).select_from(LearningTask).where(
            LearningTask.plan_id == plan_id,
            LearningTask.status == TaskStatus.completed,
        )
    )).scalar_one()

    pct = round(completed / total * 100, 1) if total > 0 else 0.0

    return {
        "plan_id": plan_id,
        "title": plan.title,
        "total_tasks": total,
        "completed_tasks": completed,
        "progress_pct": pct,
        "status": plan.status.value,
        "estimated_hours": plan.estimated_hours,
    }


async def get_review_stats(session: AsyncSession, days: int = 30) -> dict:
    """Return review statistics for the last N days."""
    from datetime import datetime, timedelta
    since = datetime.utcnow() - timedelta(days=days)

    count = (await session.execute(
        select(func.count()).select_from(ReviewRecord).where(ReviewRecord.reviewed_at >= since)
    )).scalar_one()

    avg_score = (await session.execute(
        select(func.avg(ReviewRecord.score)).where(ReviewRecord.reviewed_at >= since)
    )).scalar_one()

    return {
        "period_days": days,
        "total_reviews": count,
        "average_score": round(float(avg_score or 0), 3),
    }
