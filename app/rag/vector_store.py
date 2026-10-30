"""
Vector store management module using FAISS.
Handles building, saving, loading, and querying vector indexes.
"""
from pathlib import Path
from typing import List, Optional
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from app.config import settings
from app.rag.embeddings import get_embedding_function
from app.rag.document_loader import load_knowledge_base_documents, get_document_chunks


def build_and_save_vector_store(
    index_path: Optional[Path] = None,
    knowledge_base_dir: Optional[Path] = None,
) -> FAISS:
    """
    Loads knowledge base documents, chunks them, computes embeddings,
    builds a local FAISS index, and saves it to disk.
    """
    if index_path is None:
        index_path = settings.FAISS_INDEX_DIR
    if knowledge_base_dir is None:
        knowledge_base_dir = settings.KNOWLEDGE_BASE_DIR

    print(f"Loading documents from {knowledge_base_dir}...")
    documents = load_knowledge_base_documents(knowledge_base_dir)
    if not documents:
        raise ValueError(f"No markdown documents found in {knowledge_base_dir}!")

    print(f"Chunking {len(documents)} documents...")
    chunks = get_document_chunks(documents)
    print(f"Generated {len(chunks)} text chunks.")

    print("Generating embeddings and building FAISS index...")
    embeddings = get_embedding_function()
    vector_store = FAISS.from_documents(chunks, embeddings)

    # Ensure parent directory exists
    index_path.mkdir(parents=True, exist_ok=True)
    vector_store.save_local(str(index_path))
    print(f"FAISS index successfully saved to {index_path}")
    return vector_store


def load_vector_store(index_path: Optional[Path] = None) -> FAISS:
    """
    Loads an existing FAISS vector store from disk.
    If the index or pickle file does not exist, or fails to load,
    automatically builds it from the knowledge base documents.
    """
    if index_path is None:
        index_path = settings.FAISS_INDEX_DIR

    index_faiss = index_path / "index.faiss"
    index_pkl = index_path / "index.pkl"

    if not index_faiss.exists() or not index_pkl.exists():
        print(f"FAISS index files not found at {index_path}. Building now from knowledge base...")
        return build_and_save_vector_store(index_path=index_path)

    embeddings = get_embedding_function()
    try:
        # allow_dangerous_deserialization=True is required by LangChain for local trusted pickle files
        vector_store = FAISS.load_local(
            str(index_path),
            embeddings,
            allow_dangerous_deserialization=True,
        )
        # Verify index dimension matches the active embedding model dimension
        test_dim = len(embeddings.embed_query("dimension check"))
        if vector_store.index.d != test_dim:
            print(f"Index dimension mismatch (index has {vector_store.index.d}, model produces {test_dim}). Rebuilding...")
            return build_and_save_vector_store(index_path=index_path)
        return vector_store
    except Exception as e:
        print(f"Warning: Failed to load FAISS index from {index_path} ({e}). Rebuilding from scratch...")
        return build_and_save_vector_store(index_path=index_path)


def search_similar_chunks(
    query: str,
    k: int = 3,
    vector_store: Optional[FAISS] = None,
) -> List[Document]:
    """
    Searches the vector store for the top-k most relevant chunks matching the user's inquiry.
    """
    if vector_store is None:
        vector_store = load_vector_store()
    try:
        return vector_store.similarity_search(query, k=k)
    except Exception as e:
        print(f"Warning: Vector search failed ({e}). Rebuilding index and retrying...")
        vector_store = build_and_save_vector_store()
        return vector_store.similarity_search(query, k=k)
