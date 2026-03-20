import pytest
from unittest.mock import AsyncMock, patch
from db.models import LearningPlan, LearningTask, TaskStatus


@pytest.mark.asyncio
async def test_create_knowledge_item(db_session):
    from db.models import KnowledgeItem
    item = KnowledgeItem(title="Test Topic", content="Some content about testing.", tags=["test"])
    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(item)
    assert item.id is not None
    assert item.title == "Test Topic"


@pytest.mark.asyncio
async def test_repository_crud(db_session):
    from db.models import KnowledgeItem
    from db.repository import BaseRepository

    repo = BaseRepository(KnowledgeItem, db_session)
    item = await repo.create(title="Repo Test", content="Content", tags=[])
    assert item.id is not None

    fetched = await repo.get(item.id)
    assert fetched.title == "Repo Test"

    count = await repo.count()
    assert count >= 1
