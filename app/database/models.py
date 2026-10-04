from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database.connection import Base


class Customer(Base):
    """Stores customer profile information."""
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False, unique=True, index=True)
    created_at = Column(DateTime, server_default=func.now(), default=datetime.utcnow)

    # Relationships
    conversations = relationship("Conversation", back_populates="customer", cascade="all, delete-orphan")
    tickets = relationship("Ticket", back_populates="customer", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Customer(id={self.id}, name='{self.name}', email='{self.email}')>"


class Conversation(Base):
    """Stores user questions and AI-generated answers for audit and history."""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), default=datetime.utcnow)

    # Relationship
    customer = relationship("Customer", back_populates="conversations")

    def __repr__(self):
        return f"<Conversation(id={self.id}, customer_id={self.customer_id})>"


class Ticket(Base):
    """Stores escalated support tickets."""
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    issue = Column(Text, nullable=False)
    category = Column(String(50), nullable=False, default="Other")
    status = Column(String(50), nullable=False, default="Open")
    created_at = Column(DateTime, server_default=func.now(), default=datetime.utcnow)

    # Relationship
    customer = relationship("Customer", back_populates="tickets")

    def __repr__(self):
        return f"<Ticket(id={self.id}, customer_id={self.customer_id}, category='{self.category}', status='{self.status}')>"
