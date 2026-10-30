"""
FastAPI application entry point.
Assembles routers, database lifecycle, security, error handling, and middleware.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database.connection import init_db
from app.api import routes, ticket_routes, conversation_routes
from app.rag.vector_store import load_vector_store

logger = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager for startup and shutdown tasks."""
    print("=" * 60)
    print(f"Starting {settings.PROJECT_NAME} v{settings.VERSION} [{settings.ENVIRONMENT.upper()}]")
    print(f"Listening on: http://{settings.BACKEND_HOST}:{settings.BACKEND_PORT}")
    print("=" * 60)

    # 1. Validate configuration for production
    config_issues = settings.validate_production_settings()
    for issue in config_issues:
        print(f"[CONFIG NOTICE] {issue}")

    # 2. Ensure MySQL tables are created and initial demo customers exist
    try:
        init_db()
        from app.database.connection import seed_initial_data_if_empty
        seed_initial_data_if_empty()
        print("[+] MySQL database tables and seed data verified.")
    except Exception as e:
        print("[!] Database initialization notice: Could not connect to database on startup.")
        print("    The application will start, but database operations will fail until MySQL is accessible.")

    # 3. Ensure FAISS index exists and is warm
    try:
        load_vector_store()
        print("[+] FAISS Vector store loaded and ready.")
    except Exception as e:
        print("[!] Vector store notice: FAISS index could not be initialized on startup.")
        print("    Knowledge base answers will use offline policy rules until index is available.")

    yield
    print("Shutting down AI Customer Support System.")


# Initialize FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="A simple, cloud-ready AI Customer Support System powered by FastAPI, MySQL, LangChain, and RAG.",
    lifespan=lifespan,
)

# Exception handler to prevent stack trace leaks to API clients
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Prevents uncaught internal exceptions from leaking internal stack traces or connection details."""
    if isinstance(exc, StarletteHTTPException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    if isinstance(exc, RequestValidationError):
        return JSONResponse(status_code=422, content={"detail": exc.errors()})
    logger.error(f"Internal error processing {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please try again later."},
    )


# Configure CORS for Streamlit frontend and configured origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
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
    is_dev = settings.ENVIRONMENT == "development"
    uvicorn.run("app.main:app", host=settings.BACKEND_HOST, port=settings.BACKEND_PORT, reload=is_dev)
