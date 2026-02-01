from pathlib import Path
from typing import Dict

from pypdf import PdfReader


def load_pdf(path: str) -> Dict:
    p = Path(path)
    reader = PdfReader(str(p))

    text_parts = []
    for page in reader.pages:
        text_parts.append(page.extract_text() or "")

    return {
        "id": p.name,
        "source": str(p),
        "text": "\n".join(text_parts).strip(),
    }