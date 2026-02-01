import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
# RAG tuning knobs (start values)
CHUNK_SIZE = 900
CHUNK_OVERLAP = 150

TOP_K = 6
MIN_SCORE = 0.25  # increase to be stricter (0.30-0.40), decrease for more recall (0.15-0.25)