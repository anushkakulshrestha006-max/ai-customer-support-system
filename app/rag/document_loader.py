"""
Document loader module.
Loads customer support knowledge base markdown files and splits them into manageable chunks.
"""
from pathlib import Path
from typing import List
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.config import settings


def detect_document_category(filename: str) -> str:
    """Infers the business category from document filename."""
    name = filename.lower()
    if "payment" in name:
        return "Payment"
    elif "delivery" in name or "shipping" in name:
        return "Delivery"
    elif "refund" in name or "return" in name:
        return "Refund"
    elif "cancellation" in name:
        return "Cancellation"
    elif "account" in name or "profile" in name:
        return "Account"
    return "Other"


def load_knowledge_base_documents(directory: Path = None) -> List[Document]:
    """
    Loads all markdown (.md) documents from the knowledge base directory.
    Attaches source filename and detected category as metadata.
    """
    if directory is None:
        directory = settings.KNOWLEDGE_BASE_DIR

    documents = []
    if not directory.exists():
        print(f"Warning: Knowledge base directory '{directory}' does not exist.")
        return documents

    md_files = sorted(list(directory.glob("*.md")))
    for file_path in md_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    category = detect_document_category(file_path.name)
                    doc = Document(
                        page_content=content,
                        metadata={
                            "source": file_path.name,
                            "category": category,
                            "file_path": str(file_path),
                        },
                    )
                    documents.append(doc)
        except Exception as e:
            print(f"Error loading file {file_path}: {e}")

    return documents


def get_document_chunks(
    documents: List[Document],
    chunk_size: int = 500,
    chunk_overlap: int = 80,
) -> List[Document]:
    """
    Splits loaded documents into smaller overlapping chunks suitable for vector search.
    Chunk size 500 with overlap 80 keeps context coherent while fitting LLM context windows.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n## ", "\n### ", "\n\n", "\n", " ", ""],
    )
    return splitter.split_documents(documents)
