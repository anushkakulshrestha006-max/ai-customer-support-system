"""
Offline script to ingest knowledge base markdown documents into the FAISS vector store.
Run via: python scripts/ingest_documents.py
"""
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.rag.vector_store import build_and_save_vector_store


def main():
    print("=" * 60)
    print("NovaStore Knowledge Base - Document Ingestion")
    print("=" * 60)
    try:
        vs = build_and_save_vector_store()
        print("\nDocument ingestion and FAISS vector index creation completed successfully!")
    except Exception as e:
        print(f"\nFailed to ingest documents: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
