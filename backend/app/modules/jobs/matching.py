import re
import uuid

from pydantic import BaseModel, Field

from app.modules.candidates.model import Candidate
from app.modules.jobs.model import Job


class MatchResult(BaseModel):
    candidate_id: uuid.UUID
    job_id: uuid.UUID
    match_score: float = Field(ge=0, le=100)
    matching_skills: list[str]
    missing_skills: list[str]
    experience_match: bool
    education_match: bool
    explanation: str


class RankedMatch(BaseModel):
    candidate_id: uuid.UUID
    candidate_name: str
    match_score: float = Field(ge=0, le=100)
    matching_skills: list[str]
    missing_skills: list[str]
    experience_match: bool
    education_match: bool
    explanation: str


def _skills(value: str | None) -> list[str]:
    return [item.strip() for item in re.split(r"[,;|\n]", value or "") if item.strip()]


def _normalized(value: str) -> str:
    return re.sub(r"[^a-z0-9+#.]", "", value.lower())


def calculate_match(candidate: Candidate, job: Job) -> MatchResult:
    candidate_skills = {_normalized(skill): skill.strip() for skill in _skills(candidate.skills)}
    required = _skills(job.required_skills)
    preferred = _skills(job.preferred_skills)
    matched_required = [skill for skill in required if _normalized(skill) in candidate_skills]
    matched_preferred = [skill for skill in preferred if _normalized(skill) in candidate_skills]
    missing = [skill for skill in required if _normalized(skill) not in candidate_skills]

    required_score = len(matched_required) / len(required) if required else 1.0
    preferred_score = len(matched_preferred) / len(preferred) if preferred else 1.0
    experience_match = candidate.experience_years is not None and candidate.experience_years >= job.minimum_experience_years
    if job.maximum_experience_years is not None and candidate.experience_years is not None:
        experience_match = experience_match and candidate.experience_years <= job.maximum_experience_years
    education_match = not job.education or (
        candidate.education is not None and job.education.lower() in candidate.education.lower()
    )
    description_terms = {
        _normalized(term) for term in re.findall(r"[A-Za-z0-9+#.]+", job.description)
    }
    description_matches = sum(1 for skill in candidate_skills if skill in description_terms)
    description_score = min(description_matches / max(len(candidate_skills), 1), 1.0)
    score = 50 * required_score + 15 * preferred_score + 20 * int(experience_match) + 10 * int(education_match) + 5 * description_score
    explanation = "Candidate has strong alignment with the required skills and experience."
    if missing:
        explanation = "Candidate matches some requirements but is missing one or more required skills."
    elif not experience_match or not education_match:
        explanation = "Candidate skills align well, but experience or education requirements need review."

    return MatchResult(
        candidate_id=candidate.id,
        job_id=job.id,
        match_score=round(score, 2),
        matching_skills=matched_required + matched_preferred,
        missing_skills=missing,
        experience_match=experience_match,
        education_match=education_match,
        explanation=explanation,
    )