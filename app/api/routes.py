import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core import llm_client
from app.core.llm_client import LLMClient

router = APIRouter()

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
async def chat(request: ChatRequest):
    request_id = str(uuid.uuid4())

    if llm is None:
        raise HTTPException(status_code=500, detail="LLM client is not initialized")
    
    try:
        reply, meta = llm.chat(request.message)
        return ChatResponse(reply=reply, request_id=request_id, meta=meta)
    except Exception as e:
        raise HTTPException(status_code=500, detail= f"Error processing request: {str(e)}")

