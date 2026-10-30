from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

# Engine configuration kwargs
engine_kwargs = {
    "pool_pre_ping": True,
    "echo": False,
}

# Only configure connection pooling parameters for non-sqlite dialects
if not settings.DATABASE_URL.startswith("sqlite"):
    engine_kwargs.update({
        "pool_size": settings.DB_POOL_SIZE,
        "max_overflow": settings.DB_MAX_OVERFLOW,
        "pool_timeout": settings.DB_POOL_TIMEOUT,
        "pool_recycle": settings.DB_POOL_RECYCLE,
    })

# Create SQLAlchemy engine with resilient connection pooling for hosted MySQL
engine = create_engine(
    settings.DATABASE_URL,
    **engine_kwargs,
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
    """
    Creates all tables defined in models if they don't already exist.
    Does not drop, truncate, or overwrite existing tables or data.
    """
    from app.database import models  # noqa: F401
    Base.metadata.create_all(bind=engine)


def seed_initial_data_if_empty():
    """
    Idempotent startup helper that seeds initial demo customer profiles
    only if the customer table is currently empty.
    Preserves all existing data.
    """
    from app.database.models import Customer
    db = SessionLocal()
    try:
        count = db.query(Customer).count()
        if count == 0:
            sample_customers = [
                {"name": "Alice Sharma", "email": "alice.sharma@example.com"},
                {"name": "Bob Miller", "email": "bob.miller@example.com"},
                {"name": "Carol Davis", "email": "carol.davis@example.com"},
                {"name": "David Wilson", "email": "david.wilson@example.com"},
            ]
            for cust_data in sample_customers:
                db.add(Customer(name=cust_data["name"], email=cust_data["email"]))
            db.commit()
            print(f"[+] Seeded {len(sample_customers)} initial demo customer profiles.")
    except Exception as e:
        db.rollback()
        print(f"[*] Note: Could not auto-seed customers ({e}). Continuing startup.")
    finally:
        db.close()
