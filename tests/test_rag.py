"""
Unit tests for RAG pipeline: document loading, chunking, vector search, and QA.
Run with: pytest tests/test_rag.py
"""
import pytest
from app.rag.document_loader import load_knowledge_base_documents, get_document_chunks
from app.rag.vector_store import load_vector_store, search_similar_chunks
from app.rag.qa import classify_intent, answer_customer_question, VALID_CATEGORIES


def test_document_loader():
    """Test 1: Verify markdown knowledge base documents are loaded."""
    docs = load_knowledge_base_documents()
    assert len(docs) >= 5
    sources = [d.metadata["source"] for d in docs]
    assert "delivery_policy.md" in sources
    assert "payment_policy.md" in sources
    assert "refund_policy.md" in sources


def test_chunking():
    """Test 2: Verify documents are split into chunks with metadata preserved."""
    docs = load_knowledge_base_documents()
    chunks = get_document_chunks(docs, chunk_size=500, chunk_overlap=80)
    assert len(chunks) > len(docs)
    for chunk in chunks:
        assert "source" in chunk.metadata
        assert "category" in chunk.metadata
        assert len(chunk.page_content) > 0


def test_vector_search_delivery():
    """Test 3: Verify semantic similarity search returns relevant delivery chunks."""
    results = search_similar_chunks("How many days will standard delivery take?", k=2)
    assert len(results) > 0
    sources = [doc.metadata["source"] for doc in results]
    assert "delivery_policy.md" in sources


def test_vector_search_payment():
    """Test 4: Verify search returns payment chunks for failed payment inquiry."""
    results = search_similar_chunks("My bank debited money but the order failed", k=2)
    assert len(results) > 0
    sources = [doc.metadata["source"] for doc in results]
    assert "payment_policy.md" in sources


def test_intent_classification():
    """Test 5: Verify intent classification returns recognized category."""
    cat_delivery = classify_intent("When will my package arrive?")
    assert cat_delivery in VALID_CATEGORIES
    assert cat_delivery == "Delivery"

    cat_payment = classify_intent("I was double charged on my credit card")
    assert cat_payment in VALID_CATEGORIES
    assert cat_payment == "Payment"

    cat_refund = classify_intent("I received a broken item and want my money back")
    assert cat_refund in VALID_CATEGORIES
    assert cat_refund == "Refund"


def test_rag_answer_generation():
    """Test 6: Verify full RAG question answering pipeline."""
    category, answer, sources = answer_customer_question("Can I cancel an order after it has shipped?")
    assert category in VALID_CATEGORIES
    assert len(answer) > 10
    assert len(sources) > 0
    assert "cancellation_policy.md" in sources
