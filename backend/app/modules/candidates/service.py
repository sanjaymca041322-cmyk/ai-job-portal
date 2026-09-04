import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.candidates.model import Candidate
from app.modules.candidates.repository import CandidateRepository
from app.modules.candidates.schemas import CandidateCreate, CandidateUpdate
from app.modules.candidates.resume_schemas import ParsedResume


class DuplicateCandidateEmailError(Exception):
    pass


class CandidateService:
    def __init__(self, session: Session) -> None:
        self.repository = CandidateRepository(session)
        self.session = session

    def create_candidate(self, candidate_data: CandidateCreate) -> Candidate:
        if self.repository.get_by_email(str(candidate_data.email)) is not None:
            raise DuplicateCandidateEmailError

        candidate = Candidate(**candidate_data.model_dump())
        try:
            created_candidate = self.repository.create(candidate)
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise DuplicateCandidateEmailError from exc

        self.session.refresh(created_candidate)
        return created_candidate

    def get_candidate(self, candidate_id: uuid.UUID) -> Candidate | None:
        return self.repository.get_by_id(candidate_id)

    def get_candidates(self) -> list[Candidate]:
        return self.repository.get_all()

    def update_candidate(
        self, candidate: Candidate, candidate_data: CandidateUpdate
    ) -> Candidate:
        changes = candidate_data.model_dump(exclude_unset=True)
        if "email" in changes:
            existing_candidate = self.repository.get_by_email(str(changes["email"]))
            if existing_candidate is not None and existing_candidate.id != candidate.id:
                raise DuplicateCandidateEmailError
            changes["email"] = str(changes["email"])

        for field, value in changes.items():
            setattr(candidate, field, value)

        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise DuplicateCandidateEmailError from exc

        self.session.refresh(candidate)
        return candidate

    def delete_candidate(self, candidate: Candidate) -> None:
        self.repository.delete(candidate)
        self.session.commit()

    def update_from_resume(self, candidate: Candidate, parsed: ParsedResume) -> Candidate:
        values = {
            "email": parsed.email,
            "phone": parsed.phone,
            "location": parsed.location,
            "skills": ", ".join(parsed.skills) if parsed.skills else None,
            "experience_years": parsed.experience_years,
            "education": parsed.education,
        }
        if parsed.name:
            name_parts = parsed.name.split(maxsplit=1)
            values["first_name"] = name_parts[0]
            if len(name_parts) > 1:
                values["last_name"] = name_parts[1]
        for field, value in values.items():
            if value not in (None, "") and (field != "email" or value != candidate.email):
                setattr(candidate, field, value)
        self.session.commit()
        self.session.refresh(candidate)
        return candidate