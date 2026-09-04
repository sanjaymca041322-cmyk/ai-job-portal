import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.modules.users.model import User


TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)


@pytest.fixture(autouse=True)
def database_session():
    Base.metadata.create_all(bind=test_engine)
    session = TestSessionLocal()

    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    yield session
    session.close()
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client():
    return TestClient(app)


def user_payload(email: str = "candidate@example.com") -> dict[str, str]:
    return {
        "email": email,
        "password": "temporary-password",
        "first_name": "Ada",
        "last_name": "Lovelace",
        "role": "candidate",
    }


def test_create_user_hashes_password_and_hides_it(client: TestClient, database_session: Session) -> None:
    response = client.post("/users", json=user_payload())

    assert response.status_code == 201
    response_data = response.json()
    assert response_data["email"] == "candidate@example.com"
    assert "password_hash" not in response_data

    user = database_session.get(User, uuid.UUID(response_data["id"]))
    assert user is not None
    assert user.password_hash != "temporary-password"
    assert user.password_hash.startswith("$argon2")


def test_get_user_returns_created_user(client: TestClient) -> None:
    create_response = client.post("/users", json=user_payload())

    response = client.get(f"/users/{create_response.json()['id']}")

    assert response.status_code == 200
    assert response.json()["email"] == "candidate@example.com"
    assert "password_hash" not in response.json()


def test_get_missing_user_returns_not_found(client: TestClient) -> None:
    response = client.get(f"/users/{uuid.uuid4()}")

    assert response.status_code == 404


def test_duplicate_email_is_rejected(client: TestClient) -> None:
    client.post("/users", json=user_payload())

    response = client.post("/users", json=user_payload())

    assert response.status_code == 409


def test_invalid_role_is_rejected(client: TestClient) -> None:
    response = client.post("/users", json={**user_payload(), "role": "unknown"})

    assert response.status_code == 422