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
from app.modules.jobs.matching import calculate_match
from app.modules.jobs.model import Job


test_engine = create_engine(
    "sqlite:///:memory:",
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


def job_payload(title: str = "Backend Engineer") -> dict[str, object]:
    return {
        "title": title,
        "description": "Build Python and FastAPI services with SQL and AWS.",
        "required_skills": "Python, FastAPI, SQL",
        "preferred_skills": "AWS, Docker",
        "minimum_experience_years": 3,
        "maximum_experience_years": 8,
        "education": "Computer Science",
        "location": "Remote",
        "employment_type": "FULL_TIME",
        "salary_min": 80000,
        "salary_max": 120000,
        "status": "OPEN",
    }


def candidate(email: str, skills: str, experience: int = 5) -> Candidate:
    return Candidate(
        first_name=email.split("@")[0].title(),
        last_name="Candidate",
        email=email,
        skills=skills,
        experience_years=experience,
        education="Computer Science",
    )


def test_create_job(client: TestClient) -> None:
    response = client.post("/jobs", json=job_payload())

    assert response.status_code == 201
    assert response.json()["title"] == "Backend Engineer"
    assert response.json()["status"] == "OPEN"


def test_get_jobs(client: TestClient) -> None:
    client.post("/jobs", json=job_payload())
    client.post("/jobs", json=job_payload("Data Engineer"))

    response = client.get("/jobs")

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_job_by_id(client: TestClient) -> None:
    job_id = client.post("/jobs", json=job_payload()).json()["id"]

    response = client.get(f"/jobs/{job_id}")

    assert response.status_code == 200
    assert response.json()["id"] == job_id


def test_update_job(client: TestClient) -> None:
    job_id = client.post("/jobs", json=job_payload()).json()["id"]

    response = client.put(f"/jobs/{job_id}", json={"title": "Senior Backend Engineer"})

    assert response.status_code == 200
    assert response.json()["title"] == "Senior Backend Engineer"


def test_delete_job(client: TestClient) -> None:
    job_id = client.post("/jobs", json=job_payload()).json()["id"]

    response = client.delete(f"/jobs/{job_id}")

    assert response.status_code == 204
    assert client.get(f"/jobs/{job_id}").status_code == 404


def test_job_not_found(client: TestClient) -> None:
    response = client.get(f"/jobs/{uuid.uuid4()}")

    assert response.status_code == 404


def test_invalid_experience(client: TestClient) -> None:
    response = client.post(
        "/jobs", json={**job_payload(), "minimum_experience_years": -1}
    )

    assert response.status_code == 422


def test_invalid_salary_range(client: TestClient) -> None:
    response = client.post(
        "/jobs", json={**job_payload(), "salary_min": 120000, "salary_max": 80000}
    )

    assert response.status_code == 422


def test_candidate_job_matching(database_session: Session) -> None:
    job = Job(**job_payload())
    person = candidate("john@example.com", "Python, FastAPI, SQL, AWS")
    database_session.add_all([job, person])
    database_session.flush()

    result = calculate_match(person, job)

    assert result.match_score > 75
    assert result.experience_match is True
    assert result.education_match is True


def test_skill_matching_and_missing_skills(database_session: Session) -> None:
    job = Job(**job_payload())
    person = candidate("jane@example.com", "Python, SQL")
    database_session.add_all([job, person])
    database_session.flush()

    result = calculate_match(person, job)

    assert result.matching_skills == ["Python", "SQL"]
    assert result.missing_skills == ["FastAPI"]


def test_experience_matching(database_session: Session) -> None:
    job = Job(**job_payload())
    person = candidate("junior@example.com", "Python, FastAPI, SQL", experience=1)
    database_session.add_all([job, person])
    database_session.flush()

    result = calculate_match(person, job)

    assert result.experience_match is False


def test_candidate_ranking(client: TestClient, database_session: Session) -> None:
    job_id = client.post("/jobs", json=job_payload()).json()["id"]
    best = candidate("best@example.com", "Python, FastAPI, SQL, AWS, Docker")
    partial = candidate("partial@example.com", "Python, SQL")
    database_session.add_all([best, partial])
    database_session.commit()

    response = client.get(f"/jobs/{job_id}/matches")

    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["candidate_name"] == "Best Candidate"
    assert response.json()[0]["match_score"] > response.json()[1]["match_score"]


def test_no_candidates(client: TestClient) -> None:
    job_id = client.post("/jobs", json=job_payload()).json()["id"]

    response = client.get(f"/jobs/{job_id}/matches")

    assert response.status_code == 200
    assert response.json() == []


def test_job_not_found_for_matching(client: TestClient) -> None:
    response = client.get(f"/jobs/{uuid.uuid4()}/matches")

    assert response.status_code == 404