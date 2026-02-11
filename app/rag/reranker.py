from __future__ import annotations
from typing import List, Dict

from app.core.llm_client import LLMClient

llm = LLMClient()

SYSTEM = """You are a strict reranker.
You will be given a QUESTION and CANDIDATE PASSAGES.
Return ONLY a JSON array of integers: the best passage indices in descending relevance.
Rules:
- Choose up to N indices.
- Prefer passages that directly answer the question.
- Do not invent indices.
"""

async def rerank(question: str, candidates: List[Dict], top_n: int = 5, request_id: str = "rerank") -> List[Dict]:
    # build compact list for model
    items = []
    for i, c in enumerate(candidates):
        items.append(f"{i}: {c['text'][:400]}")  # keep short to reduce tokens

    prompt = f"""
QUESTION:
{question}

CANDIDATES:
{chr(10).join(items)}

N={top_n}

Return JSON like: [3, 0, 5]
""".strip()

    # Use your existing chat_with_tools but with no tools needed
    reply, _ = await llm.chat_with_tools(
        f"{SYSTEM}\n\n{prompt}",
        request_id=request_id,
    )

    # Parse JSON safely
    import json
    try:
        order = json.loads(reply)
        if not isinstance(order, list):
            return candidates[:top_n]
        picked = []
        for idx in order:
            if isinstance(idx, int) and 0 <= idx < len(candidates):
                picked.append(candidates[idx])
            if len(picked) >= top_n:
                break
        return picked if picked else candidates[:top_n]
    except Exception:
        return candidates[:top_n]
