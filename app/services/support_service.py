"""
Support service module.
Coordinates between RAG pipeline, LLM, and MySQL conversation logging.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.database import crud
from app.rag.qa import answer_customer_question
from app.schemas.support import AskRequest, AskResponse, ConversationResponse


def process_customer_question(request: AskRequest, db: Session) -> AskResponse:
    """
    1. Validates that customer exists in database.
    2. Runs RAG pipeline to classify category and generate answer.
    3. Persists inquiry and response in MySQL conversations table.
    4. Returns structured AskResponse.
    """
    # 1. Customer verification
    customer = crud.get_customer_by_id(db, request.customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with ID {request.customer_id} does not exist.",
        )

    # Clean question text
    clean_question = request.question.strip()
    if not clean_question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty.",
        )

    # 2. RAG pipeline execution
    category, answer, sources = answer_customer_question(clean_question)

    # 3. Database persistence
    crud.create_conversation(
        db=db,
        customer_id=customer.id,
        question=clean_question,
        answer=answer,
    )

    # 4. Return response
    return AskResponse(
        category=category,
        answer=answer,
        sources=sources,
    )


def fetch_conversation_history(
    db: Session,
    customer_id: Optional[int] = None,
    limit: int = 50,
) -> List[ConversationResponse]:
    """Retrieves conversation history from MySQL."""
    conversations = crud.get_conversations(db, customer_id=customer_id, limit=limit)
    return [ConversationResponse.model_validate(c) for c in conversations]
