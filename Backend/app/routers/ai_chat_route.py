from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
import uuid

from app.db import SessionLocal
from app.routers.ollama_client import stream_chat
from app.routers.chat_history import get_history, add_message, clear_history
from app.routers.context_builder import get_user_financial_context, build_context_block

router = APIRouter()


# ── DB dependency (same pattern as account_route.py) ──
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class ChatRequest(BaseModel):
    message: str
    session_id: str = None


class ClearRequest(BaseModel):
    session_id: str


@router.post("/chat")
async def chat(req: ChatRequest, db: Session = Depends(get_db)):
    """
    Main chat endpoint. Streams tokens back to the frontend.
    Pulls real user financial data from the DB for context.
    """

    session_id = req.session_id or str(uuid.uuid4())
    history = get_history(session_id)
    add_message(session_id, "user", req.message)

    # ── Pull real user context from DB ──
    context_block = ""
    try:
        user_context = get_user_financial_context(db)
        context_block = build_context_block(user_context)
    except Exception:
        # Chat still works even if DB context fails
        pass

    full_reply = []

    async def generate():
        yield f"SESSION:{session_id}\n"

        async for token in stream_chat(req.message, history, context_block):
            full_reply.append(token)
            yield token

        add_message(session_id, "assistant", "".join(full_reply))

    return StreamingResponse(
        generate(),
        media_type="text/plain",
        headers={
            "X-Session-ID": session_id,
            "Cache-Control": "no-cache",
        },
    )


@router.post("/chat/clear")
async def clear(req: ClearRequest):
    clear_history(req.session_id)
    return {"status": "cleared", "session_id": req.session_id}


@router.get("/chat/health")
async def health():
    return {"status": "ok", "model": "gemma3:4b"}
