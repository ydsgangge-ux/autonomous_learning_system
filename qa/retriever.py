"""Hybrid retriever: combines vector search with knowledge graph context."""
import warnings
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from vector.retriever import retrieve
from db.models import KnowledgeItem
from core.utils import get_logger

logger = get_logger(__name__)


async def hybrid_retrieve(
    query: str,
    session: AsyncSession,
    n_vector: int = 5,
    n_graph: int = 3,
) -> str:
    """
    1. Vector search for top-N docs（如果可用）
    2. Fallback to database keyword search
    3. Return combined context string
    """
    vector_results = retrieve(query, n_results=n_vector)

    # 如果向量检索失败，使用数据库关键词搜索
    if not vector_results:
        warnings.warn("向量检索不可用，使用数据库关键词搜索")
        try:
            # 简单的关键词匹配
            keywords = query.lower().split()
            result = await session.execute(
                select(KnowledgeItem).where(
                    (KnowledgeItem.status == "active")
                ).limit(5)
            )
            items = result.scalars().all()

            # 过滤包含关键词的条目
            filtered_items = []
            for item in items:
                text = f"{item.title} {item.content} {item.summary or ''}".lower()
                if any(kw in text for kw in keywords if len(kw) > 1):
                    filtered_items.append(item)

            if filtered_items:
                context_parts = []
                for item in filtered_items[:3]:
                    context_parts.append(f"[ID: {item.id}] {item.title}\n{item.summary or item.content[:300]}")
                return "\n\n".join(context_parts)
            else:
                return "未找到相关内容（向量存储已禁用，使用关键词搜索）"
        except Exception as e:
            logger.warning(f"数据库搜索失败: {e}")
            return "未找到相关内容（向量存储已禁用）"

    # Collect item IDs from vector results
    item_ids = set()
    for r in vector_results:
        doc_id = r.get("id", "")
        if doc_id.startswith("knowledge_"):
            try:
                item_ids.add(int(doc_id.split("_")[1]))
            except ValueError:
                pass

    # Fetch DB content
    all_context = []
    if item_ids:
        result = await session.execute(
            select(KnowledgeItem).where(KnowledgeItem.id.in_(item_ids))
        )
        for item in result.scalars().all():
            all_context.append(f"[ID: {item.id}] {item.title}\n{item.summary or item.content[:400]}")

    return "\n\n".join(all_context) if all_context else "未找到相关内容"
