import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.jobs.model import Job


class JobRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, job: Job) -> Job:
        self.session.add(job)
        self.session.flush()
        self.session.refresh(job)
        return job

    def get_by_id(self, job_id: uuid.UUID) -> Job | None:
        return self.session.get(Job, job_id)

    def get_all(self) -> list[Job]:
        statement = select(Job).order_by(Job.created_at, Job.id)
        return list(self.session.scalars(statement).all())

    def delete(self, job: Job) -> None:
        self.session.delete(job)