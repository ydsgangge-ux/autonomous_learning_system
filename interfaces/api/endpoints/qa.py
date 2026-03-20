from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from qa.qa_system import answer_question
from qa.dialogue import new_session_key, get_history, clear_history
from qa.advisor import get_advice

router = APIRouter()


class QuestionRequest(BaseModel):
    question: str
    session_key: str = ""
    stream: bool = False


class QuestionResponse(BaseModel):
    answer: str
    session_key: str


@router.post("/ask", response_model=QuestionResponse)
async def ask(req: QuestionRequest, db: AsyncSession = Depends(get_db)):
    key = req.session_key or new_session_key()
    if req.stream:
        generator = await answer_question(req.question, db, key, stream=True)
        return StreamingResponse(generator, media_type="text/plain",
                                  headers={"X-Session-Key": key})
    answer = await answer_question(req.question, db, key)
    return QuestionResponse(answer=answer, session_key=key)


@router.get("/history/{session_key}")
async def history(session_key: str, db: AsyncSession = Depends(get_db)):
    msgs = await get_history(db, session_key)
    return {"session_key": session_key, "messages": msgs}


@router.delete("/history/{session_key}")
async def delete_history(session_key: str, db: AsyncSession = Depends(get_db)):
    await clear_history(db, session_key)
    return {"status": "cleared"}


@router.get("/advice")
async def advice(db: AsyncSession = Depends(get_db)):
    text = await get_advice(db)
    return {"advice": text}
