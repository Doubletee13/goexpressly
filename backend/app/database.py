from __future__ import annotations
"""
app/database.py — SQLAlchemy engine, session factory, and declarative Base.

The engine is created once at import time using DATABASE_URL from settings.
SessionLocal is used as a context manager / dependency in all route handlers.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.config import settings


engine = create_engine(
    settings.database_url,
    # Keep a small pool; increase for production load
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,   # Drop stale connections automatically
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """All ORM models inherit from this shared declarative base."""
    pass
