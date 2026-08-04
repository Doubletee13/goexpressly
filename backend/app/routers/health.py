from __future__ import annotations
"""
app/routers/health.py — Simple health check endpoint.

Used by load balancers, uptime monitors, and Docker healthchecks.
Performs a lightweight DB connectivity check in addition to returning OK.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.dependencies import get_db

router = APIRouter(tags=["Health"])


@router.get("/api/health", summary="Health check")
def health_check(db: Session = Depends(get_db)):
    """
    Returns 200 OK when the application and database are reachable.
    Returns 503 if the DB connection is unavailable (exception propagates).
    """
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}
