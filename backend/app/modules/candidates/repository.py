import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.candidates.model import Candidate


class CandidateRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, candidate: Candidate) -> Candidate:
        self.session.add(candidate)
        self.session.flush()
        self.session.refresh(candidate)
        return candidate

    def get_by_id(self, candidate_id: uuid.UUID) -> Candidate | None:
        return self.session.get(Candidate, candidate_id)

    def get_by_email(self, email: str) -> Candidate | None:
        statement = select(Candidate).where(Candidate.email == email)
        return self.session.scalar(statement)

    def get_all(self) -> list[Candidate]:
        statement = select(Candidate).order_by(Candidate.created_at, Candidate.id)
        return list(self.session.scalars(statement).all())

    def delete(self, candidate: Candidate) -> None:
        self.session.delete(candidate)