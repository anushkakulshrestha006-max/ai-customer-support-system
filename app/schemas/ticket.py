from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class TicketCreate(BaseModel):
    customer_id: int = Field(..., description="ID of the customer raising the ticket")
    issue: str = Field(..., min_length=5, description="Detailed explanation of the issue")
    category: str = Field(default="Other", description="Issue category: Payment, Delivery, Refund, Cancellation, Account, Other")


class TicketResponse(BaseModel):
    id: int
    customer_id: int
    issue: str
    category: str
    status: str
    created_at: datetime
    customer_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
