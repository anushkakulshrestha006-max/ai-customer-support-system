"""
Unit tests for Database connection and CRUD operations.
Run with: pytest tests/test_database.py
"""
import pytest
from app.database.connection import SessionLocal, engine
from app.database import crud, models


@pytest.fixture(scope="module")
def db_session():
    """Provides a transactional database session for tests."""
    session = SessionLocal()
    yield session
    session.close()


def test_database_connection(db_session):
    """Test 1: Verify database connection by executing a basic query."""
    result = db_session.execute(models.Customer.__table__.select().limit(1))
    assert result is not None


def test_customers_seeded(db_session):
    """Test 2: Verify that initial seed customers exist."""
    customers = crud.get_customers(db_session, limit=10)
    assert len(customers) >= 1
    emails = [c.email for c in customers]
    assert "alice.sharma@example.com" in emails


def test_create_and_retrieve_ticket(db_session):
    """Test 3: Verify ticket creation and retrieval."""
    # Fetch first customer
    customer = crud.get_customers(db_session, limit=1)[0]
    
    # Create ticket
    ticket = crud.create_ticket(
        db=db_session,
        customer_id=customer.id,
        issue="Test issue: delivery tracking inquiry",
        category="Delivery",
        status="Open",
    )
    assert ticket.id is not None
    assert ticket.customer_id == customer.id
    assert ticket.category == "Delivery"

    # Fetch created ticket by id
    fetched = crud.get_ticket_by_id(db_session, ticket.id)
    assert fetched is not None
    assert fetched.issue == "Test issue: delivery tracking inquiry"


def test_create_and_retrieve_conversation(db_session):
    """Test 4: Verify conversation logging."""
    customer = crud.get_customers(db_session, limit=1)[0]
    conv = crud.create_conversation(
        db=db_session,
        customer_id=customer.id,
        question="How long does delivery take?",
        answer="Delivery takes 3 to 5 business days for metro areas.",
    )
    assert conv.id is not None
    assert conv.question == "How long does delivery take?"
    
    # Verify retrieval
    history = crud.get_conversations(db_session, customer_id=customer.id, limit=5)
    assert len(history) > 0
    assert any(c.id == conv.id for c in history)
