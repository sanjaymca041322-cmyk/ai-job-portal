from pydantic import BaseModel, Field


class ParsedResume(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    skills: list[str] = Field(default_factory=list)
    education: str | None = None
    experience_years: int | None = None
    work_experience: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    summary: str | None = None