"""
API endpoints for managing customer support tickets.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.schemas.ticket import TicketCreate, TicketResponse
from app.services import ticket_service

router = APIRouter(prefix="/tickets", tags=["Tickets"])


@router.post(
    "",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new support ticket",
)
def create_ticket(
    ticket_in: TicketCreate,
    db: Session = Depends(get_db),
):
    """
    Creates an escalated support ticket for an issue that couldn't be resolved automatically.
    """
    return ticket_service.create_support_ticket(ticket_data=ticket_in, db=db)


@router.get(
    "",
    response_model=List[TicketResponse],
    summary="Retrieve support tickets",
)
def list_tickets(
    customer_id: Optional[int] = Query(None, description="Optional customer ID filter"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Fetches support tickets from MySQL, ordered by newest first.
    """
    return ticket_service.get_all_tickets(db=db, customer_id=customer_id, limit=limit)


@router.get(
    "/{ticket_id}",
    response_model=TicketResponse,
    summary="Get support ticket by ID",
)
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
):
    """
    Retrieves a single support ticket by its ID.
    """
    return ticket_service.get_single_ticket(ticket_id=ticket_id, db=db)
