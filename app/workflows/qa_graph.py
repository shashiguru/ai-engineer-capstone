from __future__ import annotations

from typing import TypedDict, List, Dict, Optional, Literal
import structlog

from langgraph.graph import StateGraph, END

from app.rag.retriever import retrieve
from app.core.guardrails import is_unsafe_user_input
from app.core.rate_limit import RateLimiter
from app.core.llm_client import LLMClient
from app.core.tool_client import ToolClient

log = structlog.get_logger()

Route = Literal["rag", "tool", "hybrid", "llm", "blocked"]


class QAState(TypedDict, total=False):
    request_id: str
    user_message: str
    client_key: str

    route: Route

    # RAG
    retrieved: List[Dict]          # your retrieve() returns dicts with text/source/etc.

    # Tools (MCP)
    tool_result: Optional[str]

    # Final
    answer: str
    citations: List[Dict]
    meta: Dict


llm = LLMClient()
tools = ToolClient()
limiter = RateLimiter(max_requests=2, window_seconds=60)


# -------------------------
# Node 1: Guard + Route
# -------------------------
async def route_node(state: QAState) -> QAState:
    msg = state["user_message"]
    client_key = state.get("client_key", "unknown")

    if not limiter.allow(client_key):
        return {
            "route": "blocked",
            "answer": "Too many requests. Please slow down.",
            "citations": [],
            "meta": {"blocked": True, "reason": "rate_limited"},
        }

    # quick safety gate (cheap)
    if is_unsafe_user_input(msg):
        return {
            "route": "blocked",
            "answer": "I can’t help with that request.",
            "citations": [],
            "meta": {"blocked": True, "reason": "unsafe_input"},
        }

    m = msg.lower()

    # 🔥 Retrieval-based routing (best)
    try:
        candidates = retrieve(msg, k=3)
        top_score = candidates[0]["score"] if candidates else 0.0
    except Exception:
        top_score = 0.0

    if top_score >= 0.25:
        return {"route": "rag", "meta": {"route": "rag", "top_score": top_score}}

    # Heuristic routing (cheap + predictable).
    # Later we can replace this with a tiny LLM classifier node.
    is_math = any(x in m for x in ["*", "multiply", "add", "sum", "plus"])
    is_knowledge = any(x in m for x in [
        "policy", "sop", "document", "docs", "on-call", "runbook", "guide",
        "resume", "cv", "profile", "experience", "skills", "projects", "education",
        "summary", "strengths", "achievements"
    ])

    if is_math and is_knowledge:
        route: Route = "hybrid"
    elif is_math:
        route = "tool"
    elif is_knowledge:
        route = "rag"
    else:
        route = "llm"

    return {"route": route, "meta": {"route": route}}


# -------------------------
# Node 2: RAG Retrieve
# -------------------------
async def rag_node(state: QAState) -> QAState:
    q = state["user_message"]

    # get candidates
    results = retrieve(q, k=6)

    # ✅ NEW: filter low quality hits
    MIN_SCORE = 0.25
    strong = [r for r in results if r["score"] >= MIN_SCORE]

    citations = [
        {"rank": r["rank"], "source": r["source"], "chunk_id": r["chunk_id"], "score": r["score"]}
        for r in strong
    ]

    return {
        "retrieved": strong,
        "citations": citations,
        "meta": {**state.get("meta", {}), "retrieval_count": len(strong), "min_score": MIN_SCORE},
    }

    
# -------------------------
# Node 3: Tool execution (MCP)
# -------------------------
async def tool_node(state: QAState) -> QAState:
    """
    For now: let your LLM tool-calling loop handle tool selection.
    It will call MCP tools via ToolClient internally (Day 6 setup).
    """
    request_id = state["request_id"]
    user_message = state["user_message"]

    # This will auto-call tools (add/multiply) when needed and return final answer.
    answer, meta = await llm.chat_with_tools(user_message, request_id=request_id)
    return {"answer": answer, "meta": {**state.get("meta", {}), **meta}}


# -------------------------
# Node 0: Blocked (rate limit / guardrails)
# -------------------------
async def blocked_node(state: QAState) -> QAState:
    return {
        "answer": state.get("answer", ""),
        "citations": state.get("citations", []),
        "meta": state.get("meta", {}),
        "route": "blocked",
    }


# -------------------------
# Node 4: Synthesize using RAG context
# -------------------------
async def rag_synthesize_node(state: QAState) -> QAState:
    request_id = state["request_id"]
    q = state["user_message"]
    retrieved = state.get("retrieved", [])

    if not retrieved:
        return {
            "answer": "I don't know based on the provided documents.",
            "meta": {**state.get("meta", {}), "no_context_found": True},
        }

    context = "\n\n".join(
        [f"[{r['rank']}] ({r['source']}) {r['text']}" for r in retrieved]
    )

    prompt = f"""
        You MUST answer using ONLY the provided context.
        - If the answer is not explicitly present in the context, reply exactly:
        "I don't know based on the provided documents."
        - When you use a piece of context, cite it as [1], [2] etc based on the context rank.

        Context:
        {context}

        Question:
        {q}
        """.strip()

    answer, meta = await llm.chat_with_tools(prompt, request_id=request_id)
    return {"answer": answer, "meta": {**state.get("meta", {}), **meta}}


# -------------------------
# Node 5: Hybrid (RAG + tools)
# -------------------------
async def hybrid_node(state: QAState) -> QAState:
    """
    Hybrid strategy:
    1) Retrieve relevant context
    2) Ask LLM with that context; it may still decide to call tools (math)
    """
    request_id = state["request_id"]
    q = state["user_message"]
    retrieved = state.get("retrieved", [])

    if not retrieved:
        return {
            "answer": "I don't know based on the provided documents.",
            "meta": {**state.get("meta", {}), "no_context_found": True},
        }

    context = "\n\n".join(
        [f"[{r['rank']}] ({r['source']}) {r['text']}" for r in retrieved]
    )

    prompt = f"""
You are a helpful assistant.
- Use the provided context for policy/process facts.
- Use tools for exact calculations if needed.
- If something is missing from context, say you don't know.

Context:
{context}

User question:
{q}

Answer with citations like [1], [2] when you use context.
""".strip()

    answer, meta = await llm.chat_with_tools(prompt, request_id=request_id)
    return {"answer": answer, "meta": {**state.get("meta", {}), **meta}}


# -------------------------
# Build graph
# -------------------------
graph = StateGraph(QAState)

graph.add_node("route", route_node)
graph.add_node("blocked", blocked_node)
graph.add_node("rag_retrieve", rag_node)
graph.add_node("tool_answer", tool_node)
graph.add_node("rag_answer", rag_synthesize_node)
graph.add_node("hybrid_answer", hybrid_node)

graph.set_entry_point("route")

# Conditional routing
graph.add_conditional_edges(
    "route",
    lambda s: s.get("route", "llm"),
    {
        "blocked": "blocked",
        "rag": "rag_retrieve",
        "tool": "tool_answer",
        "hybrid": "rag_retrieve",
        "llm": "tool_answer",  # tool_answer uses llm.chat_with_tools; it will just answer without tools if none needed
    },
)

# After retrieval: decide rag vs hybrid
graph.add_conditional_edges(
    "rag_retrieve",
    lambda s: s.get("route", "rag"),
    {
        "rag": "rag_answer",
        "hybrid": "hybrid_answer",
    },
)

graph.add_edge("tool_answer", END)
graph.add_edge("rag_answer", END)
graph.add_edge("hybrid_answer", END)
graph.add_edge("blocked", END)

workflow = graph.compile()


# Public API
async def run_qa_workflow(user_message: str, request_id: str, client_key: str) -> QAState:
    result: QAState = await workflow.ainvoke(
        {"user_message": user_message, "request_id": request_id, "client_key": client_key}
    )
    return result