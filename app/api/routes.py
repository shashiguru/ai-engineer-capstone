import uuid
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from app.core import llm_client
from app.core.llm_client import LLMClient
from app.core.tool_client import ToolClient

router = APIRouter()
tool_client = ToolClient()

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

    message = req.message.lower()

    # Simple rule-based routing
    if "multiply" in message or "*" in message:
        try:
            # Extract numbers quickly
            parts = message.replace("*", " ").split()
            nums = [int(p) for p in parts if p.isdigit()]
            result = await tool_client.multiply(nums[0], nums[1])

            meta = {"tool": "multiply"}
            return ChatResponse(reply=f"Result is {result}", request_id=request_id, meta=meta)

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # Default LLM
    reply, meta = llm.chat(req.message)
    return ChatResponse(reply=reply, request_id=request_id, meta=meta)


