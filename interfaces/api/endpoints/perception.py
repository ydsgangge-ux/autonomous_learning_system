from fastapi import APIRouter, Depends, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from db.session import get_db
from db.models import KnowledgeItem
from perception.mindmap_generator import generate_mindmap, mindmap_to_text
from perception.external import summarize_external_source

router = APIRouter()


async def fetch_url_content(url: str) -> dict:
    """Fetch content from URL."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            
            # Try to extract title
            title = url
            if "<title>" in response.text:
                start = response.text.find("<title>") + 7
                end = response.text.find("</title>", start)
                if end > start:
                    title = response.text[start:end].strip()
            
            return {
                "content": response.text[:10000],
                "title": title,
                "status": "success"
            }
    except Exception as e:
        return {"content": "", "title": url, "status": "error", "error": str(e)}


class IngestURLRequest(BaseModel):
    url: str
    auto_save: bool = True


class MindmapRequest(BaseModel):
    topic: str
    content: str


@router.post("/ingest/url")
async def ingest_url(req: IngestURLRequest, db: AsyncSession = Depends(get_db)):
    """Fetch, summarize and optionally save external URL content."""
    # First fetch the URL content
    url_data = await fetch_url_content(req.url)
    if not url_data.get("content"):
        return {"status": "failed", "message": f"Could not fetch URL: {url_data.get('error', 'Unknown error')}"}
    
    # Then summarize the content (returns string summary)
    summary = await summarize_external_source(req.url, url_data["content"])
    if not summary:
        return {"status": "failed", "message": "Could not summarize URL content"}

    if req.auto_save:
        item = KnowledgeItem(
            title=url_data.get("title", req.url),
            content=url_data["content"],
            summary=summary,
            source=req.url,
            tags=[],
        )
        db.add(item)
        await db.commit()
        await db.refresh(item)
        return {"status": "saved", "knowledge_item_id": item.id, "title": item.title}

    return {"status": "summarized", "title": url_data.get("title", req.url), "summary": summary}


@router.post("/mindmap")
async def create_mindmap(req: MindmapRequest):
    """Generate a mind map for a topic."""
    mindmap = await generate_mindmap(req.topic, req.content)
    return {"mindmap": mindmap, "text": mindmap_to_text(mindmap)}


@router.post("/ingest/text")
async def ingest_text(
    title: str,
    content: str,
    tags: str = "",
    db: AsyncSession = Depends(get_db),
):
    """Ingest plain text content as a knowledge item."""
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    item = KnowledgeItem(title=title, content=content, tags=tag_list)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return {"status": "saved", "knowledge_item_id": item.id}
