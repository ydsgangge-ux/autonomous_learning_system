"""
Task runner: starts/stops scheduled background tasks using APScheduler.
"""
from apscheduler.schedulers.background import BackgroundScheduler
from background.base import BaseTask
from core.utils import get_logger

logger = get_logger(__name__)

_scheduler: BackgroundScheduler | None = None


def get_scheduler() -> BackgroundScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler(timezone="UTC")
    return _scheduler


def register_task(task: BaseTask) -> None:
    """Register a task with the scheduler."""
    scheduler = get_scheduler()
    scheduler.add_job(
        task.run,
        "interval",
        seconds=task.interval_seconds,
        id=task.name,
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    logger.info(f"Registered task '{task.name}' every {task.interval_seconds}s")


def start() -> None:
    scheduler = get_scheduler()
    if not scheduler.running:
        scheduler.start()
        logger.info("Background scheduler started.")


def stop() -> None:
    scheduler = get_scheduler()
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Background scheduler stopped.")


def list_jobs() -> list[dict]:
    scheduler = get_scheduler()
    return [
        {"id": job.id, "next_run": str(job.next_run_time)}
        for job in scheduler.get_jobs()
    ]
