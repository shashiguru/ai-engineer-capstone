from app.rag.loader import load_documents
from app.rag.chunker import chunk_documents
from app.rag.indexer import build_faiss_index
from app.core.config import CHUNK_SIZE, CHUNK_OVERLAP

def main():
    docs = load_documents("docs")
    chunks = chunk_documents(docs, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP)
    build_faiss_index(chunks, out_dir="rag_store")
    print(f"✅ Indexed {len(docs)} docs into {len(chunks)} chunks. Saved to rag_store/")

if __name__ == "__main__":
    main()