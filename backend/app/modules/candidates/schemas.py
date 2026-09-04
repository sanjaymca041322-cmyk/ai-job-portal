import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CandidateCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=30)
    location: str | None = Field(default=None, max_length=200)
    skills: str | None = None
    experience_years: int | None = Field(default=None, ge=0)
    education: str | None = None
    resume_filename: str | None = Field(default=None, max_length=255)
    resume_path: str | None = Field(default=None, max_length=500)


class CandidateUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)
    location: str | None = Field(default=None, max_length=200)
    skills: str | None = None
    experience_years: int | None = Field(default=None, ge=0)
    education: str | None = None
    resume_filename: str | None = Field(default=None, max_length=255)
    resume_path: str | None = Field(default=None, max_length=500)


class CandidateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    first_name: str
    last_name: str
    email: EmailStr
    phone: str | None
    location: str | None
    skills: str | None
    experience_years: int | None
    education: str | None
    resume_filename: str | None
    resume_path: str | None
    created_at: datetime
    updated_at: datetime