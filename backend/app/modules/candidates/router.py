import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.candidates.model import Candidate
from app.modules.candidates.schemas import CandidateCreate, CandidateResponse, CandidateUpdate
from app.modules.candidates.service import (
    CandidateService,
    DuplicateCandidateEmailError,
)
from app.modules.candidates.parser import ResumeParser
from app.modules.candidates.resume_schemas import ParsedResume
from app.modules.candidates.resume_service import (
    EmptyResumeError,
    ResumeError,
    ResumeSizeError,
    UnsupportedResumeTypeError,
    extract_text,
    store_resume,
)


router = APIRouter(prefix="/candidates", tags=["candidates"])


def get_candidate_or_404(candidate_id: uuid.UUID, db: Session) -> Candidate:
    candidate = CandidateService(db).get_candidate(candidate_id)
    if candidate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")
    return candidate


@router.post(
    "",
    response_model=CandidateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a candidate",
    description="Create a candidate record with validated contact and experience details.",
)
def create_candidate(
    candidate_data: CandidateCreate, db: Session = Depends(get_db)
) -> CandidateResponse:
    try:
        return CandidateService(db).create_candidate(candidate_data)
    except DuplicateCandidateEmailError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A candidate with this email already exists",
        ) from exc


@router.get(
    "",
    response_model=list[CandidateResponse],
    summary="List candidates",
    description="Return all candidate records ordered by creation time.",
)
def get_candidates(db: Session = Depends(get_db)) -> list[CandidateResponse]:
    return CandidateService(db).get_candidates()


@router.get(
    "/{candidate_id}",
    response_model=CandidateResponse,
    summary="Get a candidate",
)
def get_candidate(candidate_id: uuid.UUID, db: Session = Depends(get_db)) -> CandidateResponse:
    return get_candidate_or_404(candidate_id, db)


@router.put(
    "/{candidate_id}",
    response_model=CandidateResponse,
    summary="Update a candidate",
)
def update_candidate(
    candidate_id: uuid.UUID,
    candidate_data: CandidateUpdate,
    db: Session = Depends(get_db),
) -> CandidateResponse:
    candidate = get_candidate_or_404(candidate_id, db)
    try:
        return CandidateService(db).update_candidate(candidate, candidate_data)
    except DuplicateCandidateEmailError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A candidate with this email already exists",
        ) from exc


@router.delete(
    "/{candidate_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a candidate",
)
def delete_candidate(candidate_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    candidate = get_candidate_or_404(candidate_id, db)
    CandidateService(db).delete_candidate(candidate)


@router.post(
    "/{candidate_id}/resume",
    response_model=CandidateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a candidate resume",
)
async def upload_resume(
    candidate_id: uuid.UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> CandidateResponse:
    candidate = get_candidate_or_404(candidate_id, db)
    try:
        filename, path = await store_resume(str(candidate_id), file)
    except (UnsupportedResumeTypeError, EmptyResumeError, ResumeSizeError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ResumeError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    candidate.resume_filename = filename
    candidate.resume_path = path
    db.commit()
    db.refresh(candidate)
    return candidate


@router.post(
    "/{candidate_id}/resume/parse",
    response_model=ParsedResume,
    summary="Parse a candidate resume",
)
def parse_resume(candidate_id: uuid.UUID, db: Session = Depends(get_db)) -> ParsedResume:
    candidate = get_candidate_or_404(candidate_id, db)
    if not candidate.resume_path:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Candidate has no uploaded resume")
    try:
        parsed = ResumeParser().parse(extract_text(candidate.resume_path))
        CandidateService(db).update_from_resume(candidate, parsed)
        return parsed
    except EmptyResumeError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except ResumeError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc