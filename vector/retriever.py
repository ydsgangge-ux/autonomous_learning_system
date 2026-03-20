import warnings

from vector.store import search_similar


def retrieve(query: str, n_results: int = 5) -> list[dict]:
    """
    Retrieve similar documents from vector store.
    Returns list of {id, document, metadata, distance}.
    """
    try:
        return search_similar(query, n_results=n_results)
    except Exception as e:
        warnings.warn(f"向量检索失败（已禁用）: {e}")
        return []


def retrieve_as_context(query: str, n_results: int = 5, max_chars: int = 3000) -> str:
    """Retrieve and format results as a single context string for LLM."""
    try:
        results = retrieve(query, n_results=n_results)
        parts = []
        total = 0
        for r in results:
            snippet = r["document"][:500]
            total += len(snippet)
            if total > max_chars:
                break
            parts.append(f"[{r['id']}] {snippet}")
        return "\n\n".join(parts)
    except Exception as e:
        warnings.warn(f"向量上下文检索失败（已禁用）: {e}")
        return "无相关上下文可用（向量存储已禁用）"
