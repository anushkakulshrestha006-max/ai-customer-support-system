"""
API endpoints for reviewing conversation history.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.schemas.support import ConversationResponse
from app.services import support_service

router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.get(
    "",
    response_model=List[ConversationResponse],
    summary="Retrieve conversation history",
)
def list_conversations(
    customer_id: Optional[int] = Query(None, description="Optional customer ID filter"),
    limit: int = Query(50, ge=1, le=100),
    exclude_tests: bool = Query(True, description="Exclude automated test and synthetic fixture records"),
    db: Session = Depends(get_db),
):
    """
    Fetches past questions and answers logged in MySQL, ordered by newest first.
    Filters out test-only fixture records by default for normal customer-facing review.
    """
    return support_service.fetch_conversation_history(
        db=db, customer_id=customer_id, limit=limit, exclude_tests=exclude_tests
    )
