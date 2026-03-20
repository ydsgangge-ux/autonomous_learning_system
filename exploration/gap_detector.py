"""Detect knowledge gaps using LLM analysis of the knowledge graph."""
from knowledge.graph_builder import get_all_topics, find_isolated_nodes, get_graph
from llm.client import chat_completion_json
from llm.prompt_templates.templates import GAP_DETECTION
from core.utils import get_logger

logger = get_logger(__name__)


async def detect_gaps(max_gaps: int = 5) -> list[dict]:
    """
    Analyze current knowledge graph and return detected gaps.
    Returns list of {topic, reason, priority}.
    """
    topics = get_all_topics()
    isolated = find_isolated_nodes()

    if not topics:
        logger.info("No topics in knowledge graph, skipping gap detection.")
        return []

    topics_str = "\n".join(f"- {t}" for t in topics[:100])  # limit context size

    messages = [{"role": "user", "content": GAP_DETECTION.format(topics=topics_str)}]
    try:
        result = await chat_completion_json(
            messages,
            schema_hint='{"gaps": [{"topic": str, "reason": str, "priority": int}]}'
        )
        gaps = result.get("gaps", [])
        # Boost priority for isolated nodes
        isolated_titles = {get_graph().nodes[n].get("title", "") for n in isolated}
        for gap in gaps:
            if gap.get("topic") in isolated_titles:
                gap["priority"] = min(5, gap.get("priority", 3) + 1)
        return gaps[:max_gaps]
    except Exception as e:
        logger.error(f"Gap detection failed: {e}")
        return []
