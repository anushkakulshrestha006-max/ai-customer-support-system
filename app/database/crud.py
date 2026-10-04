from typing import List, Optional
from sqlalchemy.orm import Session
from app.database.models import Customer, Conversation, Ticket


# ==========================================
# CUSTOMER CRUD OPERATIONS
# ==========================================

def get_customers(db: Session, skip: int = 0, limit: int = 100) -> List[Customer]:
    """Retrieve all registered customers."""
    return db.query(Customer).offset(skip).limit(limit).all()


def get_customer_by_id(db: Session, customer_id: int) -> Optional[Customer]:
    """Retrieve a single customer by their primary key ID."""
    return db.query(Customer).filter(Customer.id == customer_id).first()


def get_customer_by_email(db: Session, email: str) -> Optional[Customer]:
    """Retrieve a customer by their unique email address."""
    return db.query(Customer).filter(Customer.email == email).first()


def create_customer(db: Session, name: str, email: str) -> Customer:
    """Create a new customer profile."""
    customer = Customer(name=name, email=email)
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


# ==========================================
# CONVERSATION CRUD OPERATIONS
# ==========================================

def create_conversation(db: Session, customer_id: int, question: str, answer: str) -> Conversation:
    """Store a customer question and the AI response."""
    conversation = Conversation(
        customer_id=customer_id,
        question=question,
        answer=answer,
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def get_conversations(db: Session, customer_id: Optional[int] = None, limit: int = 50) -> List[Conversation]:
    """
    Retrieve conversation history, optionally filtered by customer ID,
    ordered by most recent first.
    """
    query = db.query(Conversation)
    if customer_id is not None:
        query = query.filter(Conversation.customer_id == customer_id)
    return query.order_by(Conversation.created_at.desc()).limit(limit).all()


# ==========================================
# TICKET CRUD OPERATIONS
# ==========================================

def create_ticket(
    db: Session,
    customer_id: int,
    issue: str,
    category: str = "Other",
    status: str = "Open",
) -> Ticket:
    """Create and persist a new support ticket."""
    ticket = Ticket(
        customer_id=customer_id,
        issue=issue,
        category=category,
        status=status,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


def get_tickets(db: Session, customer_id: Optional[int] = None, limit: int = 50) -> List[Ticket]:
    """
    Retrieve support tickets, optionally filtered by customer ID,
    ordered by most recent first.
    """
    query = db.query(Ticket)
    if customer_id is not None:
        query = query.filter(Ticket.customer_id == customer_id)
    return query.order_by(Ticket.created_at.desc()).limit(limit).all()


def get_ticket_by_id(db: Session, ticket_id: int) -> Optional[Ticket]:
    """Retrieve a specific ticket by ID."""
    return db.query(Ticket).filter(Ticket.id == ticket_id).first()
