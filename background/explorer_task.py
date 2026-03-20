"""Background task: run knowledge gap exploration cycle."""
import asyncio
from background.base import BaseTask
from core.settings import settings


class ExplorerTask(BaseTask):
    @property
    def name(self) -> str:
        return "explorer"

    @property
    def interval_seconds(self) -> int:
        return settings.exploration_interval_seconds

    def run(self) -> None:
        self.logger.info("Running exploration cycle...")
        try:
            asyncio.run(self._async_run())
        except Exception as e:
            self.logger.error(f"Exploration task failed: {e}")

    async def _async_run(self) -> None:
        from db.session import get_async_session
        from exploration.manager import run_exploration_cycle

        async with get_async_session() as session:
            count = await run_exploration_cycle(session)
            self.logger.info(f"Exploration complete: {count} new tasks.")
