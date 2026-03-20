"""Background task: consume sync_queue and update vector store."""
import warnings
from background.base import BaseTask
from core.settings import settings


class VectorSyncTask(BaseTask):
    @property
    def name(self) -> str:
        return "vector_sync"

    @property
    def interval_seconds(self) -> int:
        return settings.vector_sync_interval_seconds

    def run(self) -> None:
        # 向量同步已禁用（Python 3.14 兼容性）
        warnings.warn("向量同步已禁用（Python 3.14兼容性问题），跳过执行")
        return

        # 以下代码在向量存储可用时执行
        # from db.session import SyncSessionLocal
        # from vector.sync import process_sync_queue
        # self.logger.info("Running vector sync...")
        # with SyncSessionLocal() as session:
        #     try:
        #         count = process_sync_queue(session)
        #         if count > 0:
        #             self.logger.info(f"Vector sync: processed {count} entries.")
        #     except Exception as e:
        #         self.logger.error(f"Vector sync failed: {e}")
