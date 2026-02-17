import json
from pathlib import Path
from typing import List, Dict, Tuple

import numpy as np
import faiss
from openai import OpenAI

from app.core.config import OPENAI_API_KEY, OPENAI_EMBED_MODEL


def embed_query(query: str) -> np.ndarray:
    client = OpenAI(api_key=OPENAI_API_KEY)
    resp = client.embeddings.create(model=OPENAI_EMBED_MODEL, input=[query])
    vec = np.array(resp.data[0].embedding, dtype="float32").reshape(1, -1)
    faiss.normalize_L2(vec)
    return vec


def _resolve_store_dir(store_dir: str) -> Path:
    p = Path(store_dir)
    if p.is_absolute():
        return p

    # Keep default store location stable regardless of current working directory.
    project_root = Path(__file__).resolve().parents[2]
    return project_root / p


def load_store(store_dir: str = "rag_store") -> Tuple[faiss.Index, List[Dict]]:
    resolved_dir = _resolve_store_dir(store_dir)
    index = faiss.read_index(str(resolved_dir / "index.faiss"))
    chunks = json.loads((resolved_dir / "chunks.json").read_text(encoding="utf-8"))
    return index, chunks


def retrieve(query: str, k: int = 5, store_dir: str = "rag_store") -> List[Dict]:
    index, chunks = load_store(store_dir)
    q = embed_query(query)
    scores, ids = index.search(q, k)

    results = []
    for rank, idx in enumerate(ids[0]):
        if idx == -1:
            continue
        c = chunks[int(idx)]
        results.append(
            {
                "rank": rank + 1,
                "score": float(scores[0][rank]),
                "chunk_id": c["chunk_id"],
                "doc_id": c["doc_id"],
                "source": c["source"],
                "text": c["text"],
            }
        )
    return results