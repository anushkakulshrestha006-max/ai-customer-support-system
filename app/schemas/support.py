from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


# ==========================================
# CUSTOMER SCHEMAS
# ==========================================

class CustomerBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Customer full name")
    email: str = Field(..., min_length=3, max_length=100, description="Customer email address")


class CustomerCreate(CustomerBase):
    pass


class CustomerResponse(CustomerBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# RAG / ASK QUESTION SCHEMAS
# ==========================================

class AskRequest(BaseModel):
    customer_id: int = Field(..., description="ID of the customer asking the question")
    question: str = Field(..., min_length=2, description="The customer's support inquiry")


class AskResponse(BaseModel):
    category: str = Field(..., description="Detected category: Payment, Delivery, Refund, Cancellation, Account, or Other")
    answer: str = Field(..., description="AI-generated support response grounded in knowledge base")
    sources: List[str] = Field(default_factory=list, description="List of knowledge base markdown source documents used")


# ==========================================
# CONVERSATION HISTORY SCHEMAS
# ==========================================

class ConversationResponse(BaseModel):
    id: int
    customer_id: int
    question: str
    answer: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
