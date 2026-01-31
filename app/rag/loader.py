from pathlib import Path
from typing import List, Dict

def load_documents(docs_dir: str = "docs") -> List[Dict]:
    """
    Returns: list of {id, source, text}
    """
    p = Path(docs_dir)
    if not p.exists():
        raise FileNotFoundError(f"Docs directory not found: {docs_dir}")

    docs = []
    for file in sorted(p.glob("**/*")):
        if file.is_file() and file.suffix.lower() in {".txt", ".md"}:
            text = file.read_text(encoding="utf-8", errors="ignore").strip()
            if text:
                docs.append(
                    {
                        "id": str(file.relative_to(p)),
                        "source": str(file),
                        "text": text,
                    }
                )
    return docs