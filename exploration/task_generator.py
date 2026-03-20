from llm.client import chat_completion_json
from llm.prompt_templates.templates import TASK_GENERATION
from core.utils import get_logger

logger = get_logger(__name__)


async def generate_tasks_for_gap(gap: dict, context: str = "") -> list[dict]:
    """
    Given a knowledge gap dict {topic, reason, priority},
    generate learning tasks.
    Returns list of {title, description, estimated_minutes}.
    """
    messages = [{
        "role": "user",
        "content": TASK_GENERATION.format(
            gap=f"{gap['topic']}: {gap.get('reason', '')}",
            context=context or "No additional context."
        )
    }]
    try:
        result = await chat_completion_json(
            messages,
            schema_hint='{"tasks": [{"title": str, "description": str, "estimated_minutes": int}]}'
        )
        return result.get("tasks", [])
    except Exception as e:
        logger.error(f"Task generation failed for gap '{gap.get('topic')}': {e}")
        return []
