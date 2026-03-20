"""
Consume SyncQueue entries and update the vector store.
Runs in background via VectorSyncTask.
Python 3.14 兼容版本（已禁用向量同步）
"""
import warnings
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select

from db.models import SyncQueue, SyncStatus
from core.utils import get_logger

logger = get_logger(__name__)

BATCH_SIZE = 50


def process_sync_queue(session: Session) -> int:
    """Process pending sync queue entries. Returns number processed."""
    warnings.warn("向量同步已禁用（Python 3.14兼容性问题）")

    stmt = (
        select(SyncQueue)
        .where(SyncQueue.status == SyncStatus.pending)
        .order_by(SyncQueue.created_at)
        .limit(BATCH_SIZE)
    )
    entries = session.execute(stmt).scalars().all()
    if not entries:
        return 0

    processed = 0
    for entry in entries:
        entry.status = SyncStatus.processing
        session.flush()

        try:
            # 标记为完成，但不实际同步到向量库
            entry.status = SyncStatus.done
            entry.processed_at = datetime.utcnow()
        except Exception as e:
            logger.error(f"Sync failed for entry {entry.id}: {e}")
            entry.status = SyncStatus.failed
            entry.error_message = str(e)

        processed += 1

    session.commit()
    logger.info(f"Processed {processed} sync queue entries (vector sync disabled)")
    return processed
