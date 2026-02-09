"""
Database configuration and session management using SQLAlchemy with PostgreSQL.
"""
import os
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base

# Database URL - using SQLite for local development
DATABASE_URL = os.environ.get(
    'DATABASE_URL',
    'sqlite:///./aggregator_clean.db'
)

# Create engine
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False},  # Needed for SQLite
    echo=False
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models
Base = declarative_base()


def get_db():
    """Get database session - use as context manager or dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    from . import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    _ensure_schema_compatibility()


def _ensure_schema_compatibility():
    """Patch missing columns for old local SQLite databases."""
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())

    if "transactions" in table_names:
        transaction_columns = {col["name"] for col in inspector.get_columns("transactions")}
        if "usd_value" not in transaction_columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE transactions ADD COLUMN usd_value FLOAT DEFAULT 0"))
