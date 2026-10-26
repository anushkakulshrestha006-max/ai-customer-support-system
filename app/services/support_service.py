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
from app.services.response_formatter import clean_conversation_record


def process_customer_question(request: AskRequest, db: Session) -> AskResponse:
    """
    1. Validates that customer exists in database.
    2. Runs RAG pipeline to classify category and generate answer.
    3. Cleans response before persisting to ensure newly stored records are clean.
    4. Persists inquiry and clean answer to MySQL conversations table.
    5. Returns structured AskResponse.
    """
    # 1. Customer verification
    customer = crud.get_customer_by_id(db, request.customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with ID {request.customer_id} does not exist.",
        )

    # Clean question text
    clean_q_raw = request.question.strip()
    if not clean_q_raw:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty.",
        )

    # 2. RAG pipeline execution
    category, raw_answer, sources = answer_customer_question(clean_q_raw)

    # Clean response to ensure newly stored responses are clean
    cleaned = clean_conversation_record(clean_q_raw, raw_answer, sources=sources)
    final_question = cleaned["question"] or clean_q_raw
    final_answer = cleaned["answer"]
    final_sources = cleaned["sources"]

    # 3. Database persistence
    crud.create_conversation(
        db=db,
        customer_id=customer.id,
        question=final_question,
        answer=final_answer,
    )

    # 4. Return response
    return AskResponse(
        category=category,
        answer=final_answer,
        sources=final_sources,
    )


def fetch_conversation_history(
    db: Session,
    customer_id: Optional[int] = None,
    limit: int = 50,
    exclude_tests: bool = False,
) -> List[ConversationResponse]:
    """
    Retrieves conversation history from MySQL and cleans the presentation
    at the response-serialization layer without modifying database records.
    When exclude_tests=True, excludes synthetic test fixture records.
    """
    fetch_limit = min(limit * 2, 200) if exclude_tests else limit
    conversations = crud.get_conversations(db, customer_id=customer_id, limit=fetch_limit)
    results = []
    for c in conversations:
        cleaned = clean_conversation_record(c.question, c.answer)
        if exclude_tests and cleaned["is_test"]:
            continue
        results.append(
            ConversationResponse(
                id=c.id,
                customer_id=c.customer_id,
                question=cleaned["question"],
                answer=cleaned["answer"],
                created_at=c.created_at,
                sources=cleaned["sources"],
                is_demo=cleaned["is_demo"],
                is_test=cleaned["is_test"],
            )
        )
        if len(results) >= limit:
            break
    return results
