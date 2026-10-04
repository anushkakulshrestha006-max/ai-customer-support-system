"""
RAG Question-Answering and Intent Classification module.
Combines vector retrieval with LLM response generation and category classification.
"""
import json
import re
from typing import Dict, List, Tuple
from langchain_core.documents import Document
from app.config import settings
from app.rag.vector_store import search_similar_chunks


VALID_CATEGORIES = ["Payment", "Delivery", "Refund", "Cancellation", "Account", "Other"]

SYSTEM_PROMPT = """You are a polite, helpful, and concise customer support assistant for NovaStore.
Answer the customer's question using ONLY the provided knowledge base context below.

Rules to follow strictly:
1. Answer only using the provided knowledge when possible.
2. Do NOT invent company policies, timelines, or procedures.
3. If the answer cannot be found in the knowledge base context, clearly state: "I'm sorry, that information is not available in our current store policies. Please feel free to raise a support ticket so our team can assist you."
4. Do NOT pretend that an action has been performed when it has not (e.g. do not say "I have cancelled your order" or "I have processed your refund").
5. Keep answers concise, clear, and customer-friendly.

Context from Knowledge Base:
{context}

Customer Question:
{question}

Answer:"""


CLASSIFICATION_PROMPT = """Classify the customer's question into EXACTLY ONE of the following categories:
- Payment
- Delivery
- Refund
- Cancellation
- Account
- Other

Question: "{question}"

Respond with ONLY a JSON object in this format:
{{"category": "<CategoryName>"}}"""


def heuristic_category_detection(question: str) -> str:
    """Fallback rule-based classification based on keywords."""
    q = question.lower()
    if any(k in q for k in ["payment", "pay", "card", "debit", "credit", "upi", "deduct", "charge", "bank", "invoice"]):
        return "Payment"
    elif any(k in q for k in ["delivery", "ship", "courier", "track", "dispatch", "arrive", "transit", "package"]):
        return "Delivery"
    elif any(k in q for k in ["refund", "return", "broken", "defective", "damaged"]):
        return "Refund"
    elif any(k in q for k in ["cancel", "cancellation", "stop order"]):
        return "Cancellation"
    elif any(k in q for k in ["account", "password", "email", "address", "profile", "login", "phone"]):
        return "Account"
    return "Other"


def classify_intent(question: str) -> str:
    """
    Uses LLM to classify customer question into one of the 6 standard categories.
    Falls back to heuristic detection if LLM key is absent or on API failure.
    """
    api_key = settings.LLM_API_KEY.strip() if settings.LLM_API_KEY else ""

    if api_key and api_key != "your_gemini_api_key_here":
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            llm = ChatGoogleGenerativeAI(
                model=settings.LLM_MODEL,
                google_api_key=api_key,
                temperature=0.0,
            )
            prompt = CLASSIFICATION_PROMPT.format(question=question)
            response = llm.invoke(prompt)
            content = response.content.strip()

            # Extract JSON block or category text
            match = re.search(r'\{.*"category"\s*:\s*"(\w+)".*\}', content, re.DOTALL | re.IGNORECASE)
            if match:
                cat = match.group(1).capitalize()
                if cat in VALID_CATEGORIES:
                    return cat

            for cat in VALID_CATEGORIES:
                if cat.lower() in content.lower():
                    return cat
        except Exception as e:
            print(f"Warning: LLM classification error ({e}). Using heuristic classification.")

    return heuristic_category_detection(question)


def answer_customer_question(question: str, top_k: int = 3) -> Tuple[str, str, List[str]]:
    """
    Core RAG workflow:
    1. Classifies the category/intent.
    2. Retrieves top-k similar chunks from FAISS.
    3. Prompts the LLM with retrieved context.
    4. Returns (category, answer, sources).
    """
    # 1. Intent / Category Detection
    category = classify_intent(question)

    # 2. Vector retrieval
    retrieved_docs: List[Document] = search_similar_chunks(question, k=top_k)

    # Extract unique source filenames
    sources = sorted(list({doc.metadata.get("source", "knowledge_base.md") for doc in retrieved_docs}))

    # Combine chunk texts for context
    context = "\n\n---\n\n".join([doc.page_content for doc in retrieved_docs])

    # 3. LLM Response Generation
    api_key = settings.LLM_API_KEY.strip() if settings.LLM_API_KEY else ""

    if api_key and api_key != "your_gemini_api_key_here":
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            llm = ChatGoogleGenerativeAI(
                model=settings.LLM_MODEL,
                google_api_key=api_key,
                temperature=0.2,
            )
            prompt = SYSTEM_PROMPT.format(context=context, question=question)
            response = llm.invoke(prompt)
            answer = response.content.strip()
            return category, answer, sources
        except Exception as e:
            answer = (
                f"Error communicating with Gemini API: {str(e)}.\n\n"
                f"Relevant policy context found:\n{context[:300]}..."
            )
            return category, answer, sources

    # Offline / Local demonstration answer when no LLM API key is configured
    answer = (
        f"[Demo Mode - Set LLM_API_KEY in .env for live Gemini generation]\n\n"
        f"Based on our {category} policy ({', '.join(sources)}):\n\n"
        f"{retrieved_docs[0].page_content if retrieved_docs else 'No matching policy found.'}"
    )
    return category, answer, sources
