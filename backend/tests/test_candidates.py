import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.modules.candidates.model import Candidate


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


def candidate_payload(email: str = "candidate@example.com") -> dict[str, object]:
    return {
        "first_name": "Ada",
        "last_name": "Lovelace",
        "email": email,
        "phone": "+1 555 0100",
        "location": "London",
        "skills": "Python, SQL",
        "experience_years": 5,
        "education": "Mathematics",
    }


def test_create_candidate(client: TestClient) -> None:
    response = client.post("/candidates", json=candidate_payload())

    assert response.status_code == 201
    assert response.json()["email"] == "candidate@example.com"
    assert response.json()["experience_years"] == 5


def test_get_all_candidates(client: TestClient) -> None:
    client.post("/candidates", json=candidate_payload())
    client.post("/candidates", json=candidate_payload("second@example.com"))

    response = client.get("/candidates")

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_candidate_by_id(client: TestClient) -> None:
    create_response = client.post("/candidates", json=candidate_payload())
    candidate_id = create_response.json()["id"]

    response = client.get(f"/candidates/{candidate_id}")

    assert response.status_code == 200
    assert response.json()["id"] == candidate_id


def test_update_candidate(client: TestClient) -> None:
    create_response = client.post("/candidates", json=candidate_payload())
    candidate_id = create_response.json()["id"]

    response = client.put(
        f"/candidates/{candidate_id}",
        json={"location": "Paris", "experience_years": 6},
    )

    assert response.status_code == 200
    assert response.json()["location"] == "Paris"
    assert response.json()["experience_years"] == 6


def test_delete_candidate(client: TestClient) -> None:
    create_response = client.post("/candidates", json=candidate_payload())
    candidate_id = create_response.json()["id"]

    response = client.delete(f"/candidates/{candidate_id}")

    assert response.status_code == 204
    assert client.get(f"/candidates/{candidate_id}").status_code == 404


def test_candidate_not_found(client: TestClient) -> None:
    response = client.get(f"/candidates/{uuid.uuid4()}")

    assert response.status_code == 404


def test_duplicate_email(client: TestClient) -> None:
    client.post("/candidates", json=candidate_payload())

    response = client.post("/candidates", json=candidate_payload())

    assert response.status_code == 409


def test_invalid_email(client: TestClient) -> None:
    response = client.post("/candidates", json=candidate_payload("not-an-email"))

    assert response.status_code == 422


def test_negative_experience_years(client: TestClient) -> None:
    response = client.post(
        "/candidates", json={**candidate_payload(), "experience_years": -1}
    )

    assert response.status_code == 422