"""
Integration tests for FastAPI endpoints using TestClient.
Run with: pytest tests/test_api.py
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test 1: Verify root endpoint returns expected structure."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "project" in data


def test_health_check_endpoint():
    """Test 2: Verify /health reports healthy status for database and vector store."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["database"] == "healthy"
    assert data["vector_store"] == "ready"


def test_get_customers():
    """Test 3: Verify /customers returns seeded list."""
    response = client.get("/customers")
    assert response.status_code == 200
    customers = response.json()
    assert isinstance(customers, list)
    assert len(customers) >= 1
    assert "name" in customers[0]
    assert "email" in customers[0]


def test_ask_question_valid():
    """Test 4: Verify /ask processes support question via RAG and returns category, answer, sources."""
    # Retrieve first customer
    cust_res = client.get("/customers")
    cust_id = cust_res.json()[0]["id"]

    payload = {
        "customer_id": cust_id,
        "question": "What is your refund policy for broken items?",
    }
    response = client.post("/ask", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "category" in data
    assert "answer" in data
    assert "sources" in data
    assert isinstance(data["sources"], list)
    assert data["category"] == "Refund"


def test_ask_question_invalid_customer():
    """Test 5: Verify /ask returns 404 for non-existent customer."""
    payload = {
        "customer_id": 999999,
        "question": "Can I cancel an order?",
    }
    response = client.post("/ask", json=payload)
    assert response.status_code == 404
    assert "not exist" in response.json()["detail"]


def test_ask_question_empty_string():
    """Test 6: Verify /ask returns validation error for blank question."""
    cust_res = client.get("/customers")
    cust_id = cust_res.json()[0]["id"]

    payload = {
        "customer_id": cust_id,
        "question": "   ",
    }
    response = client.post("/ask", json=payload)
    assert response.status_code in [400, 422]


def test_create_and_fetch_ticket():
    """Test 7: Verify /tickets creation and listing."""
    cust_res = client.get("/customers")
    cust_id = cust_res.json()[0]["id"]

    ticket_data = {
        "customer_id": cust_id,
        "issue": "Payment was deducted but order failed at gateway",
        "category": "Payment",
    }
    create_res = client.post("/tickets", json=ticket_data)
    assert create_res.status_code == 201
    ticket = create_res.json()
    assert ticket["id"] is not None
    assert ticket["category"] == "Payment"
    assert ticket["status"] == "Open"

    # Get single ticket
    get_res = client.get(f"/tickets/{ticket['id']}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == ticket["id"]


def test_get_conversations():
    """Test 8: Verify /conversations returns logged history."""
    response = client.get("/conversations")
    assert response.status_code == 200
    convs = response.json()
    assert isinstance(convs, list)
    assert len(convs) >= 1


def test_update_ticket_status_valid():
    """Test 9: Verify ticket status can be updated to valid states."""
    cust_res = client.get("/customers")
    cust_id = cust_res.json()[0]["id"]

    # Create ticket
    create_res = client.post(
        "/tickets",
        json={"customer_id": cust_id, "issue": "Testing status transition workflow", "category": "Delivery"},
    )
    assert create_res.status_code == 201
    ticket_id = create_res.json()["id"]

    # Transition to In Progress
    patch_res = client.patch(f"/tickets/{ticket_id}/status", json={"status": "In Progress"})
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "In Progress"

    # Transition to Resolved
    patch_res2 = client.patch(f"/tickets/{ticket_id}/status", json={"status": "Resolved"})
    assert patch_res2.status_code == 200
    assert patch_res2.json()["status"] == "Resolved"


def test_update_ticket_status_invalid_status():
    """Test 10: Verify 400 error when providing an unsupported status."""
    cust_res = client.get("/customers")
    cust_id = cust_res.json()[0]["id"]
    create_res = client.post(
        "/tickets",
        json={"customer_id": cust_id, "issue": "Testing invalid status rejection", "category": "Other"},
    )
    ticket_id = create_res.json()["id"]

    bad_res = client.patch(f"/tickets/{ticket_id}/status", json={"status": "InvalidStatusXYZ"})
    assert bad_res.status_code == 400
    assert "Invalid status" in bad_res.json()["detail"]


def test_update_ticket_status_not_found():
    """Test 11: Verify 404 error when ticket ID does not exist."""
    res = client.patch("/tickets/999999/status", json={"status": "Closed"})
    assert res.status_code == 404

