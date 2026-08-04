#!/usr/bin/env python
"""
scripts/seed_admin.py — Create the initial admin user.

Run once after the database is set up:
    python scripts/seed_admin.py

You will be prompted for email, full name, and password interactively.
The password is hashed with bcrypt (12 rounds) before storage.
Never run this script with the password as a CLI argument — it would
appear in shell history.
"""
import sys
import getpass

# Ensure the project root is on sys.path regardless of where the script is called from
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bcrypt
from sqlalchemy.orm import Session

from app.database import SessionLocal, engine, Base
from app.models import Admin  # triggers model registration
from app.models.admin import Admin as AdminModel


def seed_admin(db: Session) -> None:
    print("\n── GoExpressly Admin Seed ──────────────────────────────")
    email = input("Admin email: ").strip().lower()

    if not email:
        print("Error: email cannot be empty.")
        sys.exit(1)

    existing = db.query(AdminModel).filter(AdminModel.email == email).first()
    if existing:
        print(f"Error: An admin with email '{email}' already exists.")
        sys.exit(1)

    full_name = input("Full name (optional, press Enter to skip): ").strip() or None

    password = getpass.getpass("Password: ")
    confirm = getpass.getpass("Confirm password: ")

    if password != confirm:
        print("Error: passwords do not match.")
        sys.exit(1)

    if len(password) < 8:
        print("Error: password must be at least 8 characters.")
        sys.exit(1)

    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12))

    admin = AdminModel(
        email=email,
        hashed_password=hashed.decode("utf-8"),
        full_name=full_name,
        is_active=True,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)

    print(f"\n✓ Admin created successfully.")
    print(f"  ID:    {admin.id}")
    print(f"  Email: {admin.email}")
    if admin.full_name:
        print(f"  Name:  {admin.full_name}")
    print()


if __name__ == "__main__":
    # Ensure tables exist before trying to insert
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        seed_admin(db)
    finally:
        db.close()
