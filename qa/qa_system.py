"""
QA System: handles question answering with context retrieval and history.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator

from qa.retriever import hybrid_retrieve
from qa.dialogue import get_history, add_message
from llm.client import chat_completion, stream_completion
from llm.prompt_templates.templates import QA_SYSTEM
from core.utils import get_logger

logger = get_logger(__name__)


async def answer_question(
    question: str,
    session: AsyncSession,
    session_key: str,
    stream: bool = False,
) -> str | AsyncGenerator[str, None]:
    """
    Answer a question:
    1. Retrieve relevant context (hybrid)
    2. Load conversation history
    3. Call LLM with context + history
    4. Save messages to dialogue history
    """
    context = await hybrid_retrieve(question, session)
    history = await get_history(session, session_key)

    messages = history + [{"role": "user", "content": question}]
    system_prompt = QA_SYSTEM.format(context=context or "No context available.")

    await add_message(session, session_key, "user", question)

    if stream:
        async def _stream():
            full_response = []
            async for chunk in stream_completion(messages, system=system_prompt):
                full_response.append(chunk)
                yield chunk
            await add_message(session, session_key, "assistant", "".join(full_response))
        return _stream()
    else:
        response = await chat_completion(messages, system=system_prompt)
        await add_message(session, session_key, "assistant", response)
        return response
