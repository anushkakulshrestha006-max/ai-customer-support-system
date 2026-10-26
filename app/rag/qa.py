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


CATEGORY_FILE_MAP = {
    "Delivery": "delivery_policy.md",
    "Refund": "refund_policy.md",
    "Payment": "payment_policy.md",
    "Cancellation": "cancellation_policy.md",
    "Account": "account_faq.md",
}

CATEGORY_LABELS = {
    "Delivery": "our Delivery & Shipping Policy",
    "Refund": "our Returns & Refund Policy",
    "Payment": "our Payment & Billing Policy",
    "Cancellation": "our Cancellation Policy",
    "Account": "our Account & Profile Policy",
    "Other": "our store policies",
}

SYNONYMS = {
    "refund": {"refund", "refunds", "return", "returns", "exchange", "money back"},
    "return": {"refund", "refunds", "return", "returns", "exchange", "money back"},
    "broken": {"broken", "damaged", "defective", "incorrect"},
    "damaged": {"broken", "damaged", "defective", "incorrect"},
    "defective": {"broken", "damaged", "defective", "incorrect"},
    "delivery": {"delivery", "deliveries", "shipping", "ship", "courier", "package", "transit", "parcel"},
    "shipping": {"delivery", "deliveries", "shipping", "ship", "courier", "package", "transit", "parcel"},
    "cancel": {"cancel", "cancelling", "cancellation", "abort"},
    "cancellation": {"cancel", "cancelling", "cancellation", "abort"},
    "payment": {"payment", "billing", "pay", "deducted", "debited", "charge", "card", "bank"},
    "pay": {"payment", "billing", "pay", "deducted", "debited", "charge", "card", "bank"},
    "password": {"password", "reset", "login", "security"},
    "address": {"address", "shipping address", "address book"},
}

STOP_WORDS = {
    "a", "an", "the", "in", "on", "at", "to", "for", "of", "and", "or",
    "is", "are", "was", "were", "what", "how", "can", "i", "my", "your",
    "we", "do", "does", "did", "if", "an", "with", "from", "by", "about"
}


def heuristic_category_detection(question: str) -> str:
    """Rule-based classification with keyword scoring to avoid misclassifications."""
    q_lower = question.lower()
    q_words = re.findall(r"\b\w+\b", q_lower)

    category_keywords = {
        "Refund": ["refund", "refunds", "return", "returns", "broken", "defective", "damaged", "exchange", "money back"],
        "Cancellation": ["cancel", "cancelling", "cancellation", "stop order"],
        "Payment": ["payment", "pay", "card", "debit", "credit", "upi", "deduct", "charge", "bank", "invoice", "billing"],
        "Delivery": ["delivery", "deliveries", "shipping", "ship", "courier", "track", "tracking", "dispatch", "transit", "package", "parcel"],
        "Account": ["account", "password", "profile", "login", "address book"],
    }

    scores = {}
    for cat, kw_list in category_keywords.items():
        score = 0
        for kw in kw_list:
            if " " in kw:
                if kw in q_lower:
                    score += 2
            else:
                if kw in q_words:
                    score += 1
        if score > 0:
            scores[cat] = score

    if scores:
        return max(scores, key=scores.get)

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


def parse_markdown_sections(text: str) -> List[Tuple[str, str]]:
    """Splits policy markdown text into clean (heading, body) tuples, omitting disclaimers."""
    sections = []
    current_heading = "General Policy"
    current_lines = []

    for line in text.split("\n"):
        line_strip = line.strip()
        if line_strip.startswith("# ") or "fictional customer-support" in line_strip:
            continue
        if line_strip.startswith("## "):
            if current_lines:
                body = "\n".join(current_lines).strip()
                if body:
                    sections.append((current_heading, body))
                current_lines = []
            current_heading = line_strip[3:].strip()
        else:
            current_lines.append(line)

    if current_lines:
        body = "\n".join(current_lines).strip()
        if body:
            sections.append((current_heading, body))

    return sections


def generate_policy_answer(question: str, category: str, retrieved_docs: List[Document]) -> str:
    """
    Constructs a polite, professional customer-facing answer grounded strictly
    in the retrieved policy context without any technical configuration warnings.
    """
    if category == "Other" or not retrieved_docs:
        return (
            "I'm sorry, that specific information is not available in our current store policies. "
            "Our store policies currently cover shipping timelines, returns and refunds, "
            "order cancellations, accepted payment methods, and account settings.\n\n"
            "Please feel free to submit a support ticket so our support team can assist you directly with your inquiry."
        )

    # Extract words from question and expand with synonyms
    raw_words = [w for w in re.findall(r"\b\w+\b", question.lower()) if w not in STOP_WORDS]
    expanded_words = set(raw_words)
    for rw in raw_words:
        if rw in SYNONYMS:
            expanded_words.update(SYNONYMS[rw])

    # Parse sections from all retrieved docs
    all_sections = []
    for doc in retrieved_docs:
        all_sections.extend(parse_markdown_sections(doc.page_content))

    if not all_sections:
        return (
            "I'm sorry, I could not find information regarding your inquiry in our current store policies. "
            "Please feel free to create a support ticket so our customer support staff can assist you."
        )

    scored_sections = []
    for heading, body in all_sections:
        h_words = set(re.findall(r"\b\w+\b", heading.lower()))
        b_words = set(re.findall(r"\b\w+\b", body.lower()))
        # Score heading matches higher than body matches
        h_score = sum(4 for w in expanded_words if w in h_words or any(w in hw for hw in h_words))
        b_score = sum(1 for w in expanded_words if w in b_words)
        total_score = h_score + b_score
        scored_sections.append((total_score, heading, body))

    scored_sections.sort(key=lambda s: s[0], reverse=True)

    # Pick top 1 or 2 relevant sections
    top_sections = [s for s in scored_sections if s[0] > 0][:2]
    if not top_sections:
        top_sections = scored_sections[:1]

    category_label = CATEGORY_LABELS.get(category, "our store policies")
    intro = f"Based on {category_label}, here are the key details regarding your inquiry:"
    sections_text = "\n\n".join(f"**{h}**\n{b}" for _, h, b in top_sections)
    outro = f"If you need further assistance with your specific order, please feel free to create a support ticket under the **{category}** category."

    return f"{intro}\n\n{sections_text}\n\n{outro}"


def answer_customer_question(question: str, top_k: int = 3) -> Tuple[str, str, List[str]]:
    """
    Core RAG workflow:
    1. Classifies the category/intent.
    2. Retrieves top similar chunks from FAISS vector store.
    3. Prompts the LLM with retrieved context, or generates a grounded policy answer.
    4. Returns (category, answer, sources).
    """
    # 1. Intent / Category Detection
    category = classify_intent(question)

    # 2. Vector retrieval (fetch extra to allow category-prioritized re-ranking)
    retrieved_docs: List[Document] = search_similar_chunks(question, k=max(top_k, 5))

    # Re-rank: prioritize documents matching the detected category
    cat_matched = [d for d in retrieved_docs if d.metadata.get("category") == category]
    cat_others = [d for d in retrieved_docs if d.metadata.get("category") != category]
    ordered_docs = cat_matched + cat_others

    # Extract unique contributing source filenames
    sources = sorted(list({doc.metadata.get("source", "knowledge_base.md") for doc in ordered_docs[:top_k]}))
    # Ensure primary policy document for category is included in sources if present
    primary_source = CATEGORY_FILE_MAP.get(category)
    if primary_source and primary_source not in sources and any(d.metadata.get("source") == primary_source for d in ordered_docs):
        sources.insert(0, primary_source)

    # 3. LLM Response Generation or Grounded Policy Fallback
    api_key = settings.LLM_API_KEY.strip() if settings.LLM_API_KEY else ""

    if api_key and api_key != "your_gemini_api_key_here":
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            llm = ChatGoogleGenerativeAI(
                model=settings.LLM_MODEL,
                google_api_key=api_key,
                temperature=0.2,
            )
            context = "\n\n---\n\n".join([doc.page_content for doc in ordered_docs[:top_k]])
            prompt = SYSTEM_PROMPT.format(context=context, question=question)
            response = llm.invoke(prompt)
            answer = response.content.strip()
            return category, answer, sources
        except Exception as e:
            print(f"Warning: Gemini API call failed ({e}). Using local policy answer generator.")
            answer = generate_policy_answer(question, category, ordered_docs)
            return category, answer, sources

    # Offline / Local demonstration answer grounded strictly in retrieved policy documents
    answer = generate_policy_answer(question, category, ordered_docs)
    return category, answer, sources

