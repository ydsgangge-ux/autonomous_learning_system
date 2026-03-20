"""
Exploration Manager: orchestrates gap detection → task generation → DB persistence.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from db.models import ExplorationTask, TaskStatus
from exploration.gap_detector import detect_gaps
from exploration.task_generator import generate_tasks_for_gap
from exploration import cache
from core.utils import get_logger

logger = get_logger(__name__)

CACHE_KEY = "last_exploration_gaps"


async def run_exploration_cycle(session: AsyncSession) -> int:
    """
    Full exploration cycle:
    1. Detect knowledge gaps
    2. Generate learning tasks for each gap
    3. Persist new ExplorationTasks to DB
    Returns number of tasks created.
    """
    logger.info("Starting exploration cycle...")

    gaps = await detect_gaps(max_gaps=5)
    if not gaps:
        logger.info("No gaps detected.")
        return 0

    cache.set(CACHE_KEY, gaps)

    created = 0
    for gap in gaps:
        tasks = await generate_tasks_for_gap(gap)
        for task_data in tasks:
            # Avoid duplicates by topic
            existing = await session.execute(
                select(ExplorationTask).where(
                    ExplorationTask.topic == task_data["title"],
                    ExplorationTask.status == TaskStatus.PENDING,
                )
            )
            if existing.scalars().first():
                continue

            task = ExplorationTask(
                topic=task_data["title"],
                description=task_data.get("description"),
                gap_reason=gap.get("reason"),
                status=TaskStatus.PENDING,
            )
            session.add(task)
            created += 1

    await session.commit()
    logger.info(f"Exploration cycle complete: {created} tasks created.")
    return created


async def get_pending_tasks(session: AsyncSession) -> list[ExplorationTask]:
    result = await session.execute(
        select(ExplorationTask).where(ExplorationTask.status == TaskStatus.PENDING)
    )
    return result.scalars().all()
