import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.jobs.model import EmploymentType, JobStatus


class JobCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)
    required_skills: str = Field(min_length=1)
    preferred_skills: str | None = None
    minimum_experience_years: int = Field(default=0, ge=0)
    maximum_experience_years: int | None = Field(default=None, ge=0)
    education: str | None = Field(default=None, max_length=200)
    location: str | None = Field(default=None, max_length=200)
    employment_type: EmploymentType = EmploymentType.FULL_TIME
    salary_min: Decimal | None = Field(default=None, ge=0)
    salary_max: Decimal | None = Field(default=None, ge=0)
    status: JobStatus = JobStatus.DRAFT

    @model_validator(mode="after")
    def validate_ranges(self) -> "JobCreate":
        if (
            self.maximum_experience_years is not None
            and self.maximum_experience_years < self.minimum_experience_years
        ):
            raise ValueError("maximum_experience_years cannot be less than minimum_experience_years")
        if self.salary_min is not None and self.salary_max is not None and self.salary_max < self.salary_min:
            raise ValueError("salary_max cannot be less than salary_min")
        return self


class JobUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, min_length=1)
    required_skills: str | None = Field(default=None, min_length=1)
    preferred_skills: str | None = None
    minimum_experience_years: int | None = Field(default=None, ge=0)
    maximum_experience_years: int | None = Field(default=None, ge=0)
    education: str | None = Field(default=None, max_length=200)
    location: str | None = Field(default=None, max_length=200)
    employment_type: EmploymentType | None = None
    salary_min: Decimal | None = Field(default=None, ge=0)
    salary_max: Decimal | None = Field(default=None, ge=0)
    status: JobStatus | None = None


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: str
    required_skills: str
    preferred_skills: str | None
    minimum_experience_years: int
    maximum_experience_years: int | None
    education: str | None
    location: str | None
    employment_type: EmploymentType
    salary_min: Decimal | None
    salary_max: Decimal | None
    status: JobStatus
    created_at: datetime
    updated_at: datetime