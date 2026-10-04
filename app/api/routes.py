"""
Primary API routes: root, health checks, customer management, and RAG inquiry endpoint.
"""
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.config import settings
from app.database.connection import get_db
from app.database import crud
from app.schemas.support import AskRequest, AskResponse, CustomerResponse, CustomerCreate
from app.services import support_service

router = APIRouter(tags=["Support & System"])


@router.get("/", summary="Root endpoint")
def root():
    """Welcome and API metadata."""
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "documentation": "/docs",
        "status": "online",
    }


@router.get("/health", summary="System health check")
def health_check(db: Session = Depends(get_db)):
    """
    Verifies that FastAPI is running, MySQL connection is healthy,
    and FAISS vector index is accessible.
    """
    # 1. Check database connectivity
    try:
        db.execute(text("SELECT 1;"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    # 2. Check vector store existence
    index_exists = (settings.FAISS_INDEX_DIR / "index.faiss").exists()
    vector_status = "ready" if index_exists else "not_built"

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "vector_store": vector_status,
        "llm_model": settings.LLM_MODEL,
        "api_key_configured": bool(settings.LLM_API_KEY and settings.LLM_API_KEY != "your_gemini_api_key_here"),
    }


@router.get(
    "/customers",
    response_model=List[CustomerResponse],
    summary="List all registered customers",
)
def get_customers(db: Session = Depends(get_db)):
    """Fetches all customers for UI dropdown selection."""
    return crud.get_customers(db)


@router.post(
    "/customers",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new customer",
)
def create_customer(
    customer_in: CustomerCreate,
    db: Session = Depends(get_db),
):
    """Registers a new customer profile."""
    return crud.create_customer(db, name=customer_in.name, email=customer_in.email)


@router.post(
    "/ask",
    response_model=AskResponse,
    summary="Ask a customer support question via RAG",
)
def ask_question(
    request: AskRequest,
    db: Session = Depends(get_db),
):
    """
    Main RAG support endpoint:
    - Verifies customer
    - Detects intent / category
    - Retrieves top matching policy chunks from FAISS vector store
    - Synthesizes customer-friendly response via LLM
    - Persists inquiry and answer to MySQL conversations table
    - Returns structured answer and citation sources
    """
    return support_service.process_customer_question(request=request, db=db)
