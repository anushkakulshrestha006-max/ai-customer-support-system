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
    db: Session = Depends(get_db),
):
    """
    Fetches past questions and answers logged in MySQL, ordered by newest first.
    """
    return support_service.fetch_conversation_history(db=db, customer_id=customer_id, limit=limit)
