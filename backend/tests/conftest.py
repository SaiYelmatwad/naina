import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Point the ENTIRE app at the test database before any app module is
# imported. This matters: a couple of code paths (and this test suite's own
# cascade-delete test) use app.database.SessionLocal directly rather than the
# FastAPI get_db dependency, so overriding only the dependency would silently
# leave those paths pointed at the dev database.
os.environ.setdefault(
    "DATABASE_URL",
    os.environ.get(
        "TEST_DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/signalwork_test"
    ),
)

import pytest
from fastapi.testclient import TestClient

from app.database import Base, SessionLocal, engine, get_db
from app.main import app


@pytest.fixture(scope="function", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def override_get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "password123", "full_name": "Test User"},
    )
    resp = client.post(
        "/auth/login",
        data={"username": "test@example.com", "password": "password123"},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
