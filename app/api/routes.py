import uuid
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from app.core import llm_client
from app.core.llm_client import LLMClient
from app.core.tool_client import ToolClient
import structlog
from app.core.guardrails import is_unsafe_user_input

router = APIRouter()
tool_client = ToolClient()
log = structlog.get_logger()

llm = None
try:
    llm = LLMClient()
except Exception as e:
    llm = None

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str
    request_id: str
    meta: dict

@router.get("/health")
async def health() -> dict:
    return {"status": "ok"}

@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, request: Request):
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

    if llm is None:
        raise HTTPException(status_code=500, detail="LLM client not configured. Check OPENAI_API_KEY in .env")

    if is_unsafe_user_input(req.message):
        return ChatResponse(reply="I'm sorry, I can't help with that.", request_id=request_id, meta={
            "blocked": True,
            "reason": "unsafe_input",
        })
    try:
        reply, meta = await llm.chat_with_tools(req.message)

        log.info("chat_success", request_id=request_id, meta=meta)
        return ChatResponse(reply=reply, request_id=request_id, meta=meta)

    except Exception as e:
        log.error("chat_failed", request_id=request_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"LLM call failed: {e}")


