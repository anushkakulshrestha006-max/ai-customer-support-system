"""
FastAPI application entry point.
Assembles routers, database lifecycle, and middleware.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database.connection import init_db
from app.api import routes, ticket_routes, conversation_routes
from app.rag.vector_store import load_vector_store


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager for startup and shutdown tasks."""
    print("=" * 60)
    print(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    print("=" * 60)
    # Ensure MySQL tables are created
    try:
        init_db()
        print("[+] MySQL database tables verified.")
    except Exception as e:
        print(f"[!] Database initialization warning: {e}")

    # Ensure FAISS index exists and is warm
    try:
        load_vector_store()
        print("[+] FAISS Vector store loaded and ready.")
    except Exception as e:
        print(f"[!] Vector store warning: {e}")

    yield
    print("Shutting down AI Customer Support System.")


# Initialize FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="A simple, interview-ready AI Customer Support System powered by FastAPI, MySQL, LangChain, and RAG.",
    lifespan=lifespan,
)

# Configure CORS for local development and Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(routes.router)
app.include_router(ticket_routes.router)
app.include_router(conversation_routes.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.BACKEND_HOST, port=settings.BACKEND_PORT, reload=True)
