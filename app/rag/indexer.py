import json
from pathlib import Path
from typing import List, Dict

import numpy as np
import faiss
from openai import OpenAI

from app.core.config import OPENAI_API_KEY, OPENAI_EMBED_MODEL


def embed_texts(texts: List[str]) -> np.ndarray:
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY missing in .env")

    client = OpenAI(api_key=OPENAI_API_KEY)

    # Batch embeddings to reduce overhead
    resp = client.embeddings.create(
        model=OPENAI_EMBED_MODEL,
        input=texts,
    )

    vectors = np.array([e.embedding for e in resp.data], dtype="float32")
    return vectors


def build_faiss_index(chunks: List[Dict], out_dir: str = "rag_store") -> None:
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    texts = [c["text"] for c in chunks]
    vectors = embed_texts(texts)  # shape: (N, dim)

    dim = vectors.shape[1]
    index = faiss.IndexFlatIP(dim)  # cosine-like if vectors are normalized
    # Normalize for cosine similarity
    faiss.normalize_L2(vectors)
    index.add(vectors)

    faiss.write_index(index, str(Path(out_dir) / "index.faiss"))

    with open(Path(out_dir) / "chunks.json", "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)