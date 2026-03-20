"""SQLAlchemy event hooks to enqueue sync tasks."""
from sqlalchemy import event
from db.models import KnowledgeNode, SyncQueue
from db.session import AsyncSessionLocal

def register_events():
    """Register all SQLAlchemy event listeners."""
    # 事件监听器已通过装饰器注册
    pass

@event.listens_for(KnowledgeNode, 'after_insert')
def receive_after_insert(mapper, connection, target):
    """Queue a sync task after insert."""
    _enqueue_sync(target.id, 'create')

@event.listens_for(KnowledgeNode, 'after_update')
def receive_after_update(mapper, connection, target):
    """Queue a sync task after update."""
    _enqueue_sync(target.id, 'update')

@event.listens_for(KnowledgeNode, 'after_delete')
def receive_after_delete(mapper, connection, target):
    """Queue a sync task after delete."""
    _enqueue_sync(target.id, 'delete')

def _enqueue_sync(node_id: int, action: str):
    """Insert a row into sync_queue (synchronous, runs in same transaction)."""
    # Note: we use the connection that is part of the ongoing transaction
    # This is safe because it's the same connection used for the main operation
    from sqlalchemy import insert
    stmt = insert(SyncQueue).values(node_id=node_id, action=action)
    connection.execute(stmt)
