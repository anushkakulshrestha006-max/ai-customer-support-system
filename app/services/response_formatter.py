"""
Response Formatter & Normalization Module.
Cleans raw/historical AI responses, removes debug/demo-mode banners,
extracts policy references, and normalizes customer-facing presentation.
"""
import re
from typing import Any, Dict, List, Optional

SOURCE_TITLE_MAP = {
    "delivery_policy.md": "Delivery & Shipping Policy",
    "cancellation_policy.md": "Cancellation Policy",
    "refund_policy.md": "Returns & Refund Policy",
    "payment_policy.md": "Payment & Billing Policy",
    "account_faq.md": "Account & Profile FAQ",
}


def get_readable_source_title(filename: str) -> str:
    """
    Converts a knowledge base markdown filename into a clean, human-readable title.
    Example: 'delivery_policy.md' -> 'Delivery & Shipping Policy'
             'cancellation_policy.md' -> 'Cancellation Policy'
    """
    if not filename:
        return ""
    clean_fn = filename.strip()
    if clean_fn in SOURCE_TITLE_MAP:
        return SOURCE_TITLE_MAP[clean_fn]

    # Handle paths like "policies/delivery_policy.md"
    base_fn = clean_fn.replace("\\", "/").split("/")[-1]
    if base_fn in SOURCE_TITLE_MAP:
        return SOURCE_TITLE_MAP[base_fn]

    # Fallback: remove extension, replace underscores/hyphens, title case
    title = base_fn.replace(".md", "").replace("_", " ").replace("-", " ").strip().title()
    return title


def clean_question(question: Optional[str]) -> str:
    """
    Cleans raw customer question text:
    - Removes visual Q: or Question: prefixes (plain text or markdown bold)
    - Strips surrounding whitespace
    - Handles repeated prefixes gracefully
    """
    if not question:
        return ""
    q = str(question).strip()
    while True:
        new_q = re.sub(
            r"^(?:\*\*Q:\*\*|\*\*Question:\*\*|Q:|Question:)\s*",
            "",
            q,
            flags=re.IGNORECASE,
        ).strip()
        if new_q == q:
            break
        q = new_q
    return q


def clean_answer(
    answer: Optional[str],
    sources: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Cleans support response text for customer presentation:
    1. Detects and removes internal demo-mode warnings and environment variable setup messages.
    2. Strips raw A: / Answer: visual prefixes.
    3. Removes technical policy-introduction lines that embed internal filenames
       (e.g., 'Based on our Delivery policy (cancellation_policy.md, delivery_policy.md):')
       while extracting those filenames into the sources list.
    4. Formats policy sources into readable document titles without inventing unassociated sources.
    5. Preserves all substantive policy text, bullet points, and guidance.
    """
    if not answer:
        return {
            "answer": "",
            "sources": list(sources or []),
            "readable_sources": [get_readable_source_title(s) for s in (sources or [])],
            "is_demo": False,
        }

    raw_text = str(answer).strip()

    # Detect demo mode indicators
    is_demo = bool(
        re.search(r"\[Demo Mode[^\]]*\]", raw_text, re.IGNORECASE)
        or "LLM_API_KEY" in raw_text
        or "local demo mode" in raw_text.lower()
    )

    # 1. Strip raw A: / Answer: prefixes from the beginning
    text = raw_text
    while True:
        new_text = re.sub(
            r"^(?:\*\*A:\*\*|\*\*Answer:\*\*|A:|Answer:)\s*",
            "",
            text.strip(),
            flags=re.IGNORECASE,
        )
        if new_text == text:
            break
        text = new_text

    # 2. Strip [Demo Mode ...] blocks
    text = re.sub(r"\[Demo Mode[^\]]*\]\s*", "", text, flags=re.IGNORECASE)

    # 3. Process lines to strip debug info and extract policy references from technical intro lines
    extracted_sources: List[str] = []
    cleaned_lines: List[str] = []

    for line in text.splitlines():
        line_strip = line.strip()

        # Remove lines exposing environment variable names or setup instructions
        if "LLM_API_KEY" in line_strip or "Set LLM_API_KEY" in line_strip:
            is_demo = True
            continue

        # Check for technical policy intro line embedding .md filenames, e.g.:
        # 'Based on our Delivery policy (cancellation_policy.md, delivery_policy.md):'
        # 'Based on our Refund policy (delivery_policy.md, payment_policy.md, refund_policy.md):'
        # '(cancellation_policy.md, delivery_policy.md)'
        md_matches = re.findall(r"\b([\w-]+\.md)\b", line_strip)
        is_technical_policy_intro = bool(
            md_matches
            and (
                re.match(r"^Based on (?:our\s+)?[^:]*?\([^)]*\.md[^)]*\):?", line_strip, re.IGNORECASE)
                or re.match(r"^\(?[\w\s,._-]+\.md(?:[\s,._-]+[\w\s,._-]+\.md)*\)?$", line_strip, re.IGNORECASE)
                or re.match(r"^(?:Sources?|Policies|References):\s*[\w\s,._-]+\.md", line_strip, re.IGNORECASE)
            )
        )

        if is_technical_policy_intro:
            for m in md_matches:
                if m not in extracted_sources:
                    extracted_sources.append(m)
            # Omit the technical policy-intro line with raw filenames from the displayed answer
            continue

        cleaned_lines.append(line)

    cleaned_answer = "\n".join(cleaned_lines).strip()

    # Re-check for any leftover leading A: prefixes after stripping
    while True:
        new_ans = re.sub(
            r"^(?:\*\*A:\*\*|\*\*Answer:\*\*|A:|Answer:)\s*",
            "",
            cleaned_answer,
            flags=re.IGNORECASE,
        ).strip()
        if new_ans == cleaned_answer:
            break
        cleaned_answer = new_ans

    # Combine provided sources with extracted sources, preserving unique order
    final_sources = list(sources or [])
    for src in extracted_sources:
        if src not in final_sources:
            final_sources.append(src)

    readable_sources = [get_readable_source_title(s) for s in final_sources]

    return {
        "answer": cleaned_answer,
        "sources": final_sources,
        "readable_sources": readable_sources,
        "is_demo": is_demo,
    }


def is_test_record(question: Optional[str], answer: Optional[str] = None) -> bool:
    """
    Identifies whether a conversation record was generated by automated unit/integration
    test suites or synthetic test fixtures rather than genuine customer interaction.

    Distinction criteria:
    - Matches known synthetic test harness prefixes (e.g., 'Test Q from...', 'Test Question #...', '[TEST]...')
    - Matches synthetic dummy test stub answers (e.g., 'Answer for C1', 'Historical answer preservation test')
    - Does NOT flag legitimate customer inquiries that naturally contain the word 'test'
      (e.g., 'Can I test the product before returning?', 'How do I test my order tracking?').
    """
    if not question and not answer:
        return False

    q = (question or "").strip()
    a = (answer or "").strip()

    # Synthetic test fixture question patterns (anchored to start of question or test markers)
    test_q_patterns = [
        r"^(?:\*\*Q:\*\*\s*|Q:\s*)?Test\s+Q\b",             # e.g., 'Test Q from C1', 'Test Q2'
        r"^\[TEST\]",                                         # e.g., '[TEST] Can I cancel'
        r"^(?:\*\*Q:\*\*\s*|Q:\s*)?Test\s+Question\s*(?:#|\d|from|for|:)",  # e.g., 'Test Question #1'
        r"^(?:\*\*Q:\*\*\s*|Q:\s*)?Test\s+fixture\b",
        r"^(?:\*\*Q:\*\*\s*|Q:\s*)?Test\s+record\b",
        r"^(?:\*\*Q:\*\*\s*|Q:\s*)?Is this historical record safe\?",        # Specific test suite preservation assertion
    ]
    for pat in test_q_patterns:
        if re.search(pat, q, re.IGNORECASE):
            return True

    # Synthetic test fixture stub answers
    test_a_patterns = [
        r"^Answer\s+for\s+C\d+$",                             # e.g., 'Answer for C1', 'Answer for C2'
        r"^Test\s+answer\b",
        r"Historical answer preservation test",
    ]
    for pat in test_a_patterns:
        if re.search(pat, a, re.IGNORECASE):
            return True

    return False


def clean_conversation_record(
    question: Optional[str],
    answer: Optional[str],
    sources: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Cleans an entire conversation record (both question and answer).
    Returns a unified dict with cleaned question, cleaned answer,
    sources, readable_sources, demo mode flag, and test record flag.
    """
    clean_q = clean_question(question)
    cleaned_ans = clean_answer(answer, sources=sources)

    return {
        "question": clean_q,
        "answer": cleaned_ans["answer"],
        "sources": cleaned_ans["sources"],
        "readable_sources": cleaned_ans["readable_sources"],
        "is_demo": cleaned_ans["is_demo"],
        "is_test": is_test_record(question, answer),
    }
