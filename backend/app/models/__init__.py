from __future__ import annotations
"""
app/models/__init__.py
Imports all models so that Base.metadata has them registered
before create_all is called in main.py's lifespan.
"""
from app.models.admin import Admin          # noqa: F401
from app.models.package import Package      # noqa: F401
from app.models.tracking_event import TrackingEvent  # noqa: F401
from app.models.email_log import EmailLog   # noqa: F401
