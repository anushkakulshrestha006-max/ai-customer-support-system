from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

# Create SQLAlchemy engine with connection pool recycle to avoid stale MySQL connections
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False,
)

# SessionLocal is the factory for creating database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative Base for all database models
Base = declarative_base()


def get_db():
    """
    FastAPI dependency that yields a database session for each request
    and ensures it is safely closed after the request completes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables defined in models if they don't already exist."""
    from app.database import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
