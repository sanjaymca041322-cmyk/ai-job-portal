import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.candidates.repository import CandidateRepository
from app.modules.jobs.matching import MatchResult, RankedMatch, calculate_match
from app.modules.jobs.schemas import JobCreate, JobResponse, JobUpdate
from app.modules.jobs.service import InvalidJobRangeError, JobService


router = APIRouter(prefix="/jobs", tags=["jobs"])


def get_job_or_404(job_id: uuid.UUID, db: Session):
    job = JobService(db).get_job(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED, summary="Create a job")
def create_job(job_data: JobCreate, db: Session = Depends(get_db)) -> JobResponse:
    return JobService(db).create_job(job_data)


@router.get("", response_model=list[JobResponse], summary="List jobs")
def get_jobs(db: Session = Depends(get_db)) -> list[JobResponse]:
    return JobService(db).get_jobs()


@router.get("/{job_id}", response_model=JobResponse, summary="Get a job")
def get_job(job_id: uuid.UUID, db: Session = Depends(get_db)) -> JobResponse:
    return get_job_or_404(job_id, db)


@router.put("/{job_id}", response_model=JobResponse, summary="Update a job")
def update_job(job_id: uuid.UUID, job_data: JobUpdate, db: Session = Depends(get_db)) -> JobResponse:
    job = get_job_or_404(job_id, db)
    try:
        return JobService(db).update_job(job, job_data)
    except InvalidJobRangeError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a job")
def delete_job(job_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    JobService(db).delete_job(get_job_or_404(job_id, db))


@router.get("/{job_id}/matches", response_model=list[RankedMatch], summary="Rank candidates for a job")
def get_job_matches(job_id: uuid.UUID, db: Session = Depends(get_db)) -> list[RankedMatch]:
    job = get_job_or_404(job_id, db)
    candidates = CandidateRepository(db).get_all()
    matches = [(candidate, calculate_match(candidate, job)) for candidate in candidates]
    matches.sort(key=lambda item: item[1].match_score, reverse=True)
    return [
        RankedMatch(
            candidate_id=match.candidate_id,
            candidate_name=f"{candidate.first_name} {candidate.last_name}",
            match_score=match.match_score,
            matching_skills=match.matching_skills,
            missing_skills=match.missing_skills,
            experience_match=match.experience_match,
            education_match=match.education_match,
            explanation=match.explanation,
        )
        for candidate, match in matches
    ]