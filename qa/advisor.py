"""Generate personalized learning advice."""
from sqlalchemy.ext.asyncio import AsyncSession

from planning.monitor import get_review_stats
from llm.client import chat_completion
from llm.prompt_templates.templates import LEARNING_ADVICE
from core.utils import get_logger

logger = get_logger(__name__)


async def get_advice(session: AsyncSession, plan_id: int | None = None) -> str:
    """Generate personalized learning advice based on progress."""
    stats = await get_review_stats(session, days=7)
    progress = f"Reviews in last 7 days: {stats['total_reviews']}, avg score: {stats['average_score']}"

    if stats["total_reviews"] == 0:
        activity = "No recent activity."
    elif stats["average_score"] < 0.5:
        activity = "Struggling with recall - many low scores."
    elif stats["average_score"] > 0.8:
        activity = "Excellent recall performance."
    else:
        activity = "Moderate recall performance."

    messages = [{
        "role": "user",
        "content": LEARNING_ADVICE.format(progress=progress, activity=activity)
    }]

    try:
        return await chat_completion(messages, temperature=0.6)
    except Exception as e:
        logger.error(f"Failed to generate advice: {e}")
        return "Unable to generate advice at this time. Keep up with your reviews!"
