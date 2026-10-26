"""
Regression tests for conversation history UI formatting and cleaning.
Tests:
1. Exact demo-mode prefix removal.
2. Removal of raw Q: and A: prefixes.
3. Removal of technical policy-intro line with filenames while retaining policy guidance.
4. Separate readable policy references generation without inventing sources.
5. Verification that existing database records are not modified when serialized/displayed.
6. Edge case handling (empty strings, None, multiple lines, repeated prefixes).
7. Integration with /conversations API endpoint.
8. Streamlit UI Conversation History rendering via AppTest.
"""
import pytest
from fastapi.testclient import TestClient
from streamlit.testing.v1 import AppTest
from app.main import app
from app.database.connection import SessionLocal
from app.database import crud
from app.services.response_formatter import (
    clean_question,
    clean_answer,
    clean_conversation_record,
    get_readable_source_title,
    is_test_record,
    SOURCE_TITLE_MAP,
)
from app.services import support_service


# ----------------------------------------------------------------------
# 1. Exact Demo-Mode Prefix Removal
# ----------------------------------------------------------------------
def test_exact_demo_mode_prefix_removal():
    """Verify exact demo-mode warning is stripped and is_demo flag is raised."""
    raw_text = (
        "[Demo Mode - Set LLM_API_KEY in .env for live Gemini generation]\n\n"
        "Based on our Delivery policy (cancellation_policy.md, delivery_policy.md):\n\n"
        "Standard delivery takes 3 to 5 business days for metro locations."
    )
    result = clean_answer(raw_text)

    assert result["is_demo"] is True
    assert "[Demo Mode" not in result["answer"]
    assert "LLM_API_KEY" not in result["answer"]
    assert ".env" not in result["answer"]
    assert "Gemini generation" not in result["answer"]
    assert "Standard delivery takes 3 to 5 business days for metro locations." in result["answer"]


# ----------------------------------------------------------------------
# 2. Removal of Raw Q: and A: Display Prefixes
# ----------------------------------------------------------------------
def test_raw_question_prefixes_removal():
    """Verify all variations of Q: prefixes are stripped from questions."""
    cases = [
        ("Q: How long does standard delivery take?", "How long does standard delivery take?"),
        ("**Q:** How long does standard delivery take?", "How long does standard delivery take?"),
        ("Question: What is your refund policy?", "What is your refund policy?"),
        ("**Question:** What is your refund policy?", "What is your refund policy?"),
        ("  **Q:**   How do I reset my password?  ", "How do I reset my password?"),
        ("**Q:** Q: Nested question prefix", "Nested question prefix"),
        ("How long does standard delivery take?", "How long does standard delivery take?"),
    ]
    for raw_q, expected in cases:
        assert clean_question(raw_q) == expected


def test_raw_answer_prefixes_removal():
    """Verify all variations of A: prefixes are stripped from answers."""
    cases = [
        ("A: Orders arrive within 3-5 business days.", "Orders arrive within 3-5 business days."),
        ("**A:** Orders arrive within 3-5 business days.", "Orders arrive within 3-5 business days."),
        ("Answer: Returns are accepted within 30 days.", "Returns are accepted within 30 days."),
        ("**Answer:** Returns are accepted within 30 days.", "Returns are accepted within 30 days."),
        ("**A:** A: Double prefix response", "Double prefix response"),
        ("Orders arrive within 3-5 business days.", "Orders arrive within 3-5 business days."),
    ]
    for raw_a, expected in cases:
        res = clean_answer(raw_a)
        assert res["answer"] == expected


# ----------------------------------------------------------------------
# 3. Removal of Technical Policy-Intro Line Retaining Guidance
# ----------------------------------------------------------------------
def test_technical_policy_intro_line_removal_retaining_guidance():
    """
    Verify lines like 'Based on our Delivery policy (cancellation_policy.md, delivery_policy.md):'
    are stripped while retaining the policy content beneath it.
    """
    raw_answer = (
        "Based on our Delivery policy (cancellation_policy.md, delivery_policy.md):\n\n"
        "## Order Tracking\n"
        "- Once your package has dispatched, you will receive an SMS and email.\n"
        "- Real-time updates become active within 12 hours."
    )
    res = clean_answer(raw_answer)

    assert "Based on our Delivery policy" not in res["answer"]
    assert "cancellation_policy.md" not in res["answer"]
    assert "delivery_policy.md" not in res["answer"]
    assert "## Order Tracking" in res["answer"]
    assert "- Once your package has dispatched, you will receive an SMS and email." in res["answer"]
    assert "- Real-time updates become active within 12 hours." in res["answer"]
    assert "cancellation_policy.md" in res["sources"]
    assert "delivery_policy.md" in res["sources"]


# ----------------------------------------------------------------------
# 4. Readable Policy References & No Invented Sources
# ----------------------------------------------------------------------
def test_readable_policy_title_mapping():
    """Verify markdown filenames map to clean professional titles."""
    assert get_readable_source_title("delivery_policy.md") == "Delivery & Shipping Policy"
    assert get_readable_source_title("cancellation_policy.md") == "Cancellation Policy"
    assert get_readable_source_title("refund_policy.md") == "Returns & Refund Policy"
    assert get_readable_source_title("payment_policy.md") == "Payment & Billing Policy"
    assert get_readable_source_title("account_faq.md") == "Account & Profile FAQ"
    assert get_readable_source_title("custom_rules.md") == "Custom Rules"


def test_no_invented_sources_when_unassociated():
    """Verify that when no sources are provided or embedded, sources remains empty."""
    clean_text = "I'm sorry, that specific information is not available in our store policies."
    res = clean_answer(clean_text)
    assert res["sources"] == []
    assert res["readable_sources"] == []


def test_sources_passed_explicitly():
    """Verify explicitly passed source metadata is converted to readable titles."""
    res = clean_answer(
        "Standard delivery is 3-5 business days.",
        sources=["delivery_policy.md", "cancellation_policy.md"],
    )
    assert res["sources"] == ["delivery_policy.md", "cancellation_policy.md"]
    assert res["readable_sources"] == ["Delivery & Shipping Policy", "Cancellation Policy"]


# ----------------------------------------------------------------------
# 5. Database Records Not Modified When Read
# ----------------------------------------------------------------------
def test_old_database_records_not_modified():
    """
    Verify that reading and cleaning historical records through support_service
    does NOT overwrite, delete, or modify the underlying database records.
    """
    db = SessionLocal()
    try:
        customer = crud.get_customers(db, limit=1)[0]
        raw_db_answer = (
            "[Demo Mode - Set LLM_API_KEY in .env for live Gemini generation]\n\n"
            "Based on our Delivery policy (cancellation_policy.md, delivery_policy.md):\n\n"
            "Historical answer preservation test."
        )
        conv = crud.create_conversation(
            db=db,
            customer_id=customer.id,
            question="**Q:** Is this historical record safe?",
            answer=raw_db_answer,
        )
        conv_id = conv.id

        # Fetch via support_service (which cleans at serialization layer)
        fetched = support_service.fetch_conversation_history(db=db, customer_id=customer.id, limit=20)
        target = [c for c in fetched if c.id == conv_id][0]

        # Serialized output must be clean
        assert target.question == "Is this historical record safe?"
        assert "[Demo Mode" not in target.answer
        assert "Historical answer preservation test." in target.answer
        assert target.is_demo is True
        assert "delivery_policy.md" in target.sources

        # Query raw record directly from DB to verify raw value was NOT modified
        raw_db_record = crud.get_conversation_by_id(db, conv_id)
        assert raw_db_record.question == "**Q:** Is this historical record safe?"
        assert "[Demo Mode - Set LLM_API_KEY in .env for live Gemini generation]" in raw_db_record.answer
        assert "cancellation_policy.md, delivery_policy.md" in raw_db_record.answer

    finally:
        db.close()


# ----------------------------------------------------------------------
# 6. Edge Case Handling
# ----------------------------------------------------------------------
def test_edge_cases_empty_and_multiline():
    """Verify empty responses, None, multiple lines, and special characters handle gracefully."""
    res_empty = clean_conversation_record("", "")
    assert res_empty["question"] == ""
    assert res_empty["answer"] == ""
    assert res_empty["sources"] == []
    assert res_empty["is_demo"] is False

    res_none = clean_conversation_record(None, None)
    assert res_none["question"] == ""
    assert res_none["answer"] == ""
    assert res_none["sources"] == []
    assert res_none["is_demo"] is False

    multiline_answer = (
        "Here are the instructions:\n"
        "1. Go to your Account page.\n"
        "2. Click 'Edit Profile'.\n\n"
        "> Note: Email updates require OTP verification."
    )
    res_multi = clean_answer(multiline_answer)
    assert res_multi["answer"] == multiline_answer
    assert res_multi["is_demo"] is False


# ----------------------------------------------------------------------
# 7. Integration: API /conversations Endpoint Returns Clean Output
# ----------------------------------------------------------------------
def test_api_conversations_endpoint_returns_clean_cards():
    """Verify GET /conversations returns clean question/answer fields with is_demo and sources."""
    client = TestClient(app)
    response = client.get("/conversations", params={"limit": 20})
    assert response.status_code == 200
    convs = response.json()
    assert isinstance(convs, list)
    assert len(convs) > 0

    for c in convs:
        assert not c["question"].startswith("Q:")
        assert not c["question"].startswith("**Q:**")
        assert not c["answer"].startswith("A:")
        assert not c["answer"].startswith("**A:**")
        assert "[Demo Mode" not in c["answer"]
        assert "LLM_API_KEY" not in c["answer"]
        assert "sources" in c
        assert "is_demo" in c


# ----------------------------------------------------------------------
# 8. Customer ID Association: correct IDs on conversation records
# ----------------------------------------------------------------------
def test_customer_id_association_on_conversations():
    """Verify each conversation record has the correct customer_id stored."""
    db = SessionLocal()
    try:
        customers = crud.get_customers(db, limit=5)
        if len(customers) >= 2:
            c1, c2 = customers[0], customers[1]
            conv1 = crud.create_conversation(db=db, customer_id=c1.id, question="Test Q from C1", answer="Answer for C1")
            conv2 = crud.create_conversation(db=db, customer_id=c2.id, question="Test Q from C2", answer="Answer for C2")

            # Verify stored associations
            assert conv1.customer_id == c1.id
            assert conv2.customer_id == c2.id

            # Verify filtering
            c1_convs = crud.get_conversations(db, customer_id=c1.id, limit=50)
            c2_convs = crud.get_conversations(db, customer_id=c2.id, limit=50)
            assert any(c.id == conv1.id for c in c1_convs)
            assert not any(c.id == conv2.id for c in c1_convs)
            assert any(c.id == conv2.id for c in c2_convs)
            assert not any(c.id == conv1.id for c in c2_convs)

            # Verify via service layer
            fetched1 = support_service.fetch_conversation_history(db=db, customer_id=c1.id, limit=50)
            fetched2 = support_service.fetch_conversation_history(db=db, customer_id=c2.id, limit=50)
            t1 = [f for f in fetched1 if f.id == conv1.id]
            t2 = [f for f in fetched2 if f.id == conv2.id]
            assert len(t1) == 1
            assert t1[0].customer_id == c1.id
            assert len(t2) == 1
            assert t2[0].customer_id == c2.id
    finally:
        db.close()


# ----------------------------------------------------------------------
# 9. No raw backend URL on dashboard
# ----------------------------------------------------------------------
def test_no_raw_backend_url_on_dashboard():
    """Verify the dashboard page does not display the raw FastAPI URL."""
    at = AppTest.from_file("streamlit_app/app.py", default_timeout=15)
    at.run()
    # Dashboard is the default page
    all_markdown = " ".join([m.value for m in at.markdown])
    assert "127.0.0.1:8001" not in all_markdown
    assert "FastAPI @" not in all_markdown


# ----------------------------------------------------------------------
# 10. UI AppTest: Conversation History Page Renders Cleanly
# ----------------------------------------------------------------------
def test_streamlit_conversation_history_page_renders_cleanly():
    """Verify Streamlit Conversation History page loads without error."""
    at = AppTest.from_file("streamlit_app/app.py", default_timeout=15)
    at.run()
    at.sidebar.radio[0].set_value("Conversation History").run()
    assert len(at.exception) == 0

    headers = [m.value for m in at.markdown if "Conversation History" in m.value]
    assert len(headers) > 0


# ----------------------------------------------------------------------
# 11. Test Record vs Legitimate Customer Inquiry Distinction
# ----------------------------------------------------------------------
def test_is_test_record_distinguishes_synthetic_from_genuine():
    """
    Verify synthetic test fixture records are flagged while legitimate
    customer inquiries containing the word 'test' are NOT flagged.
    """
    # Synthetic test records -> True
    assert is_test_record("Test Q from C1", "Answer for C1") is True
    assert is_test_record("Test Q from C2", "Answer for C2") is True
    assert is_test_record("**Q:** Is this historical record safe?", "Historical answer preservation test.") is True
    assert is_test_record("[TEST] Can I cancel an order?", "Mock answer") is True
    assert is_test_record("Test Question #1: status check", "Some response") is True
    assert is_test_record("Test fixture for delivery", "Delivery response") is True

    # Legitimate customer questions containing 'test' -> False
    assert is_test_record("Can I test the product before returning it?", "Returns are accepted within 30 days.") is False
    assert is_test_record("How do I test my order tracking number?", "You can check your shipment status...") is False
    assert is_test_record("I want to test if my payment method is supported.", "We accept Visa, Mastercard...") is False
    assert is_test_record("How long does standard delivery take?", "Delivery takes 3 to 5 business days.") is False
    assert is_test_record("What is your refund policy?", "Our refund policy allows 30 days...") is False


# ----------------------------------------------------------------------
# 12. API /conversations Excludes Test Records By Default
# ----------------------------------------------------------------------
def test_api_conversations_excludes_test_records_by_default():
    """Verify /conversations excludes test fixture records by default."""
    client = TestClient(app)
    response = client.get("/conversations", params={"limit": 50})
    assert response.status_code == 200
    convs = response.json()
    assert len(convs) > 0

    # Ensure no test records appear in default response
    for c in convs:
        assert not c["question"].startswith("Test Q from")
        assert not c["question"].startswith("**Q:** Is this historical record safe?")
        assert c["answer"] != "Answer for C1"
        assert c["answer"] != "Answer for C2"
        assert c.get("is_test") is False
