import uuid

from sqlalchemy.orm import Session

from app.modules.jobs.model import Job
from app.modules.jobs.repository import JobRepository
from app.modules.jobs.schemas import JobCreate, JobUpdate


class InvalidJobRangeError(ValueError):
    pass


class JobService:
    def __init__(self, session: Session) -> None:
        self.repository = JobRepository(session)
        self.session = session

    def create_job(self, job_data: JobCreate) -> Job:
        job = Job(**job_data.model_dump())
        created_job = self.repository.create(job)
        self.session.commit()
        self.session.refresh(created_job)
        return created_job

    def get_job(self, job_id: uuid.UUID) -> Job | None:
        return self.repository.get_by_id(job_id)

    def get_jobs(self) -> list[Job]:
        return self.repository.get_all()

    def update_job(self, job: Job, job_data: JobUpdate) -> Job:
        changes = job_data.model_dump(exclude_unset=True)
        minimum = changes.get("minimum_experience_years", job.minimum_experience_years)
        maximum = changes.get("maximum_experience_years", job.maximum_experience_years)
        salary_min = changes.get("salary_min", job.salary_min)
        salary_max = changes.get("salary_max", job.salary_max)
        if maximum is not None and maximum < minimum:
            raise InvalidJobRangeError(
                "maximum_experience_years cannot be less than minimum_experience_years"
            )
        if salary_min is not None and salary_max is not None and salary_max < salary_min:
            raise InvalidJobRangeError("salary_max cannot be less than salary_min")

        for field, value in changes.items():
            setattr(job, field, value)
        self.session.commit()
        self.session.refresh(job)
        return job

    def delete_job(self, job: Job) -> None:
        self.repository.delete(job)
        self.session.commit()