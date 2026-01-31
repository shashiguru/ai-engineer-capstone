from typing import List, Dict

def chunk_text(text: str, chunk_size: int = 900, overlap: int = 150) -> List[str]:
    chunks = []
    start = 0
    n = len(text)

    while start < n:
        end = min(start + chunk_size, n)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end == n:
            break
        start = max(0, end - overlap)

    return chunks


def chunk_documents(docs: List[Dict], chunk_size: int = 900, overlap: int = 150) -> List[Dict]:
    """
    Returns list of {chunk_id, doc_id, source, text}
    """
    out = []
    for d in docs:
        parts = chunk_text(d["text"], chunk_size=chunk_size, overlap=overlap)
        for i, c in enumerate(parts):
            out.append(
                {
                    "chunk_id": f'{d["id"]}::chunk{i}',
                    "doc_id": d["id"],
                    "source": d["source"],
                    "text": c,
                }
            )
    return out