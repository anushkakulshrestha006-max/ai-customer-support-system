"""
API endpoints for managing customer support tickets.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.config import settings
from app.database.connection import get_db
from app.schemas.ticket import TicketCreate, TicketResponse, TicketStatusUpdate
from app.services import ticket_service

router = APIRouter(prefix="/tickets", tags=["Tickets"])


def verify_admin_access(x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key")):
    """
    Validates admin credentials for ticket modifications.
    In production mode, a valid ADMIN_API_KEY is strictly required. Missing or empty keys
    lock down ticket status changes rather than bypassing authorization.
    In development mode without an ADMIN_API_KEY configured, allows open demo access.
    """
    configured_key = settings.ADMIN_API_KEY.strip()

    if settings.ENVIRONMENT == "production":
        if not configured_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized: Admin access is locked because ADMIN_API_KEY is not configured in production.",
            )
        if not x_admin_key or x_admin_key.strip() != configured_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized: Admin access required. Provide a valid 'X-Admin-Key' header.",
            )
        return True

    # Development mode: enforce only when an ADMIN_API_KEY is explicitly configured
    if configured_key:
        if not x_admin_key or x_admin_key.strip() != configured_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized: Admin access required. Provide a valid 'X-Admin-Key' header.",
            )
    return True


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


@router.patch(
    "/{ticket_id}/status",
    response_model=TicketResponse,
    summary="Update support ticket status",
)
def update_ticket_status(
    ticket_id: int,
    status_update: TicketStatusUpdate,
    db: Session = Depends(get_db),
    _authorized: bool = Depends(verify_admin_access),
):
    """
    Updates the status of an existing support ticket.
    Allowed statuses: Open, In Progress, Resolved, Closed.
    Protected by X-Admin-Key when ADMIN_API_KEY is configured in production.
    """
    return ticket_service.update_ticket_status(ticket_id=ticket_id, status_update=status_update, db=db)
