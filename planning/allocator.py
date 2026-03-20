"""Task decomposition and time estimation."""
from llm.client import chat_completion_json
from core.utils import get_logger

logger = get_logger(__name__)


async def decompose_goal(goal: str, total_hours: float = 10.0) -> list[dict]:
    """
    Break a learning goal into ordered tasks with time estimates.
    Returns list of {title, description, estimated_minutes, order}.
    """
    messages = [{
        "role": "user",
        "content": (
            f"Break down this learning goal into concrete tasks.\n"
            f"Goal: {goal}\n"
            f"Total available time: {total_hours} hours\n\n"
            "Return JSON: "
            '{"tasks": [{"title": str, "description": str, "estimated_minutes": int, "order": int}]}'
        )
    }]
    try:
        result = await chat_completion_json(messages)
        tasks = result.get("tasks", [])
        # Validate total time roughly fits
        total_estimated = sum(t.get("estimated_minutes", 30) for t in tasks)
        max_minutes = total_hours * 60
        if total_estimated > max_minutes:
            # Scale down proportionally
            scale = max_minutes / total_estimated
            for t in tasks:
                t["estimated_minutes"] = max(10, round(t["estimated_minutes"] * scale))
        return tasks
    except Exception as e:
        logger.error(f"Goal decomposition failed: {e}")
        return []


def estimate_completion_date(tasks: list[dict], daily_hours: float = 1.0) -> str:
    """Estimate when tasks will be completed given daily study hours."""
    from datetime import datetime, timedelta
    total_minutes = sum(t.get("estimated_minutes", 30) for t in tasks)
    total_days = total_minutes / (daily_hours * 60)
    completion = datetime.utcnow() + timedelta(days=total_days)
    return completion.strftime("%Y-%m-%d")
