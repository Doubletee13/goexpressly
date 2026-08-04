"""
tests/conftest.py — Shared pytest fixtures.

Uses an in-memory SQLite database so tests need no external Postgres instance.
SQLAlchemy's create_all creates the schema fresh for each test session.

The `client` fixture provides an httpx.TestClient wired to the FastAPI app
with the overridden get_db dependency pointing at the test DB.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.core.dependencies import get_db
from app.main import app

# SQLite in-memory — no external process required
TEST_DATABASE_URL = "sqlite:///./test.db"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create all tables once for the test session; drop them after."""
    import app.models  # noqa: F401 — register all models with Base
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def db():
    """Provide a transactional test session that rolls back after each test."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture()
def client(db):
    """
    httpx TestClient with get_db overridden to use the test session.
    Ensures every test uses an isolated, rolled-back transaction.
    """
    def override_get_db():
        try:
            yield db
        finally:
            pass  # rollback handled by the db fixture

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def seeded_admin(db):
    """Create and return a test admin record (hashed password: 'TestPass1!')."""
    import bcrypt
    from app.models.admin import Admin

    hashed = bcrypt.hashpw(b"TestPass1!", bcrypt.gensalt(rounds=4))
    admin = Admin(
        email="test@goexpressly.com",
        hashed_password=hashed.decode(),
        full_name="Test Admin",
        is_active=True,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


@pytest.fixture()
def auth_headers(client, seeded_admin):
    """Login and return Authorization headers for the seeded admin."""
    resp = client.post(
        "/api/auth/login",
        json={"email": "test@goexpressly.com", "password": "TestPass1!"},
    )
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
