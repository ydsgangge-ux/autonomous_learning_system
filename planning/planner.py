"""Main planning controller: create plans, assign tasks, schedule reviews."""
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from db.models import LearningPlan, LearningTask, ReviewRecord, TaskStatus
from db.repository import BaseRepository
from planning.allocator import decompose_goal
from planning.scheduler import sm2
from core.utils import get_logger

logger = get_logger(__name__)


async def create_plan(
    session: AsyncSession,
    title: str,
    goal: str,
    description: str = "",
    priority: int = 5,
    daily_hours: float = 1.0,
) -> LearningPlan:
    """Create a full learning plan with decomposed tasks."""
    tasks_data = await decompose_goal(goal, total_hours=daily_hours * 30)

    plan = LearningPlan(
        title=title,
        description=description,
        goal=goal,
        priority=priority,
        estimated_hours=sum(t.get("estimated_minutes", 30) for t in tasks_data) / 60,
        status=TaskStatus.PENDING,
    )
    session.add(plan)
    await session.flush()

    for t in tasks_data:
        task = LearningTask(
            plan_id=plan.id,
            title=t["title"],
            description=t.get("description", ""),
            estimated_minutes=t.get("estimated_minutes", 30),
            order=t.get("order", 0),
            status=TaskStatus.PENDING,
        )
        session.add(task)

    await session.commit()
    await session.refresh(plan)
    logger.info(f"Created plan '{title}' with {len(tasks_data)} tasks.")
    return plan


async def record_review(
    session: AsyncSession,
    task_id: int,
    score: float,
    knowledge_item_id: int | None = None,
) -> ReviewRecord:
    """Record a review and compute next review date via SM-2."""
    # Get latest review for this task
    latest = (await session.execute(
        select(ReviewRecord)
        .where(ReviewRecord.task_id == task_id)
        .order_by(ReviewRecord.reviewed_at.desc())
        .limit(1)
    )).scalars().first()

    result = sm2(
        score=score,
        repetitions=latest.repetitions if latest else 0,
        ease_factor=latest.ease_factor if latest else 2.5,
        interval_days=latest.interval_days if latest else 1,
    )

    record = ReviewRecord(
        task_id=task_id,
        knowledge_item_id=knowledge_item_id,
        score=score,
        next_review_at=result.next_review_at,
        interval_days=result.interval_days,
        repetitions=result.repetitions,
        ease_factor=result.ease_factor,
        reviewed_at=datetime.utcnow(),
    )
    session.add(record)
    await session.commit()
    return record


async def get_due_tasks(session: AsyncSession, limit: int = 20) -> list[LearningTask]:
    """Return tasks due for review or not yet started."""
    now = datetime.utcnow()
    result = await session.execute(
        select(LearningTask)
        .where(LearningTask.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]))
        .where(
            (LearningTask.scheduled_at == None) | (LearningTask.scheduled_at <= now)
        )
        .order_by(LearningTask.order)
        .limit(limit)
    )
    return result.scalars().all()
