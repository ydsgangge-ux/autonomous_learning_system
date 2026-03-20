"""Manage conversation history in the database."""
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from db.models import DialogueSession, DialogueMessage
from core.utils import get_logger

logger = get_logger(__name__)

MAX_HISTORY_MESSAGES = 20   # keep last N messages per session


def new_session_key() -> str:
    return str(uuid.uuid4())


async def get_or_create_session(session: AsyncSession, session_key: str) -> DialogueSession:
    result = await session.execute(
        select(DialogueSession).where(DialogueSession.session_key == session_key)
    )
    dlg = result.scalars().first()
    if not dlg:
        dlg = DialogueSession(session_key=session_key)
        session.add(dlg)
        await session.flush()
    return dlg


async def add_message(
    session: AsyncSession,
    session_key: str,
    role: str,
    content: str,
) -> None:
    dlg = await get_or_create_session(session, session_key)
    msg = DialogueMessage(session_id=dlg.id, role=role, content=content)
    session.add(msg)
    await session.commit()


async def get_history(
    session: AsyncSession,
    session_key: str,
    max_messages: int = MAX_HISTORY_MESSAGES,
) -> list[dict]:
    """Return message history as list of {role, content} dicts."""
    result = await session.execute(
        select(DialogueMessage)
        .join(DialogueSession)
        .where(DialogueSession.session_key == session_key)
        .order_by(DialogueMessage.created_at.desc())
        .limit(max_messages)
    )
    messages = result.scalars().all()
    # Return in chronological order
    return [{"role": m.role, "content": m.content} for m in reversed(messages)]


async def clear_history(session: AsyncSession, session_key: str) -> None:
    result = await session.execute(
        select(DialogueSession).where(DialogueSession.session_key == session_key)
    )
    dlg = result.scalars().first()
    if dlg:
        await session.delete(dlg)
        await session.commit()
