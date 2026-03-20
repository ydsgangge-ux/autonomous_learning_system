"""
Startup/shutdown of background tasks.
Called from FastAPI lifespan context manager in app.py.
"""
from background.task_runner import register_task, start, stop
from background.explorer_task import ExplorerTask
from background.vector_sync_task import VectorSyncTask
from core.utils import get_logger

logger = get_logger(__name__)


def start_background_tasks() -> None:
    """Register all tasks and start the scheduler."""
    register_task(VectorSyncTask())
    register_task(ExplorerTask())
    start()
    logger.info("All background tasks started.")


def stop_background_tasks() -> None:
    """Gracefully stop the scheduler."""
    stop()
    logger.info("All background tasks stopped.")
