"""
Ticket service module.
Coordinates ticket creation, retrieval, and customer validation with MySQL.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.database import crud
from app.schemas.ticket import TicketCreate, TicketResponse, TicketStatusUpdate

ALLOWED_STATUSES = ["Open", "In Progress", "Resolved", "Closed"]



def create_support_ticket(ticket_data: TicketCreate, db: Session) -> TicketResponse:
    """
    Validates customer and creates a new support ticket in MySQL.
    """
    # Verify customer exists
    customer = crud.get_customer_by_id(db, ticket_data.customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cannot create ticket: Customer with ID {ticket_data.customer_id} not found.",
        )

    clean_issue = ticket_data.issue.strip()
    if not clean_issue:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Issue description cannot be empty.",
        )

    ticket = crud.create_ticket(
        db=db,
        customer_id=customer.id,
        issue=clean_issue,
        category=ticket_data.category or "Other",
        status="Open",
    )

    resp = TicketResponse.model_validate(ticket)
    resp.customer_name = customer.name
    return resp


def get_all_tickets(
    db: Session,
    customer_id: Optional[int] = None,
    limit: int = 50,
) -> List[TicketResponse]:
    """Retrieves tickets from MySQL with customer name included."""
    tickets = crud.get_tickets(db, customer_id=customer_id, limit=limit)
    result = []
    for t in tickets:
        resp = TicketResponse.model_validate(t)
        if t.customer:
            resp.customer_name = t.customer.name
        result.append(resp)
    return result


def get_single_ticket(ticket_id: int, db: Session) -> TicketResponse:
    """Retrieves a single ticket by its primary key ID."""
    ticket = crud.get_ticket_by_id(db, ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Support ticket #{ticket_id} not found.",
        )
    resp = TicketResponse.model_validate(ticket)
    if ticket.customer:
        resp.customer_name = ticket.customer.name
    return resp


def update_ticket_status(ticket_id: int, status_update: TicketStatusUpdate, db: Session) -> TicketResponse:
    """Validates status and updates the ticket in MySQL."""
    normalized_status = None
    for allowed in ALLOWED_STATUSES:
        if status_update.status.strip().lower() == allowed.lower():
            normalized_status = allowed
            break

    if not normalized_status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status '{status_update.status}'. Allowed statuses: {', '.join(ALLOWED_STATUSES)}.",
        )

    ticket = crud.update_ticket_status(db, ticket_id=ticket_id, status=normalized_status)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Support ticket #{ticket_id} not found.",
        )

    resp = TicketResponse.model_validate(ticket)
    if ticket.customer:
        resp.customer_name = ticket.customer.name
    return resp

