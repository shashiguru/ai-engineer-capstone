import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.rag.retriever import retrieve

# Add your own questions here (mix resume + non-resume)
QUESTIONS = [
    "What are my key skills?",
    "Summarize my experience in 3 bullets.",
    "What companies have I worked for?",
    "What is the population of Mars?",  # should NOT retrieve anything strong
]

def main():
    out = []
    for q in QUESTIONS:
        hits = retrieve(q, k=6)
        top = hits[0]["score"] if hits else 0.0
        out.append({"question": q, "top_score": top, "top_source": hits[0]["source"] if hits else None})

        print("\nQ:", q)
        print("Top score:", round(top, 4))
        for h in hits[:3]:
            print(f"  - score={h['score']:.4f} source={h['source']} chunk={h['chunk_id']}")

    print("\nJSON summary:")
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()