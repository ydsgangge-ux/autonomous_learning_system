"""Placeholder for external knowledge retrieval (web search, APIs)."""
from llm.client import llm_client

async def search_web(query: str) -> str:
    """Search the web for information."""
    # TODO: Implement using a search API
    return f"Results for {query}"

async def summarize_external_source(url: str, content: str) -> str:
    """Summarize external source content using LLM."""
    prompt = f"""请总结以下网页内容，提取关键信息：

{content[:2000]}

请提供一个简洁的总结："""
    messages = [{"role": "user", "content": prompt}]
    result = await llm_client.generate(messages)
    return result
