from __future__ import annotations
"""
app/utils/id_generator.py — Unique tracking ID generator.

Format: GX-XXXXXXXXXX
  - "GX"  prefix (GoExpressly brand identifier)
  - 10 random characters from uppercase letters + digits
  - ~35 trillion possible values; collision probability at 1M records ≈ 1 in 35B

Uses `secrets.choice` (cryptographically secure PRNG) so IDs are
non-sequential, non-guessable, and safe to expose publicly.

A DB collision check is performed to guarantee uniqueness before returning.
In practice this loop will never iterate more than once at realistic scale.
"""
import secrets
import string

from sqlalchemy.orm import Session


_ALPHABET = string.ascii_uppercase + string.digits  # A-Z0-9
_ID_LENGTH = 10
_PREFIX = "GX-"


def _generate_candidate() -> str:
    """Generate a single random candidate tracking ID."""
    random_part = "".join(secrets.choice(_ALPHABET) for _ in range(_ID_LENGTH))
    return f"{_PREFIX}{random_part}"


def generate_tracking_id(db: Session) -> str:
    """
    Generate a unique tracking ID, guaranteed not to already exist in the DB.
    Retries automatically on the astronomically unlikely collision.
    """
    # Import here to avoid circular imports at module load time
    from app.models.package import Package

    while True:
        candidate = _generate_candidate()
        exists = db.query(Package).filter(Package.tracking_id == candidate).first()
        if not exists:
            return candidate
