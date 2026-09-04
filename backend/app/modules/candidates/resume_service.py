import re
import uuid
from pathlib import Path

from docx import Document
from fastapi import UploadFile
from pypdf import PdfReader

from app.core.config import settings


class ResumeError(Exception):
    pass


class UnsupportedResumeTypeError(ResumeError):
    pass


class EmptyResumeError(ResumeError):
    pass


class ResumeSizeError(ResumeError):
    pass


class ResumeStorageError(ResumeError):
    pass


def allowed_extensions() -> set[str]:
    return {
        extension.strip().lower()
        if extension.strip().startswith(".")
        else f".{extension.strip().lower()}"
        for extension in settings.allowed_resume_extensions.split(",")
        if extension.strip()
    }


def validate_resume_type(filename: str, content_type: str | None) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix not in allowed_extensions():
        raise UnsupportedResumeTypeError("Only PDF and DOCX resumes are supported")

    expected_types = {
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
    if content_type and content_type not in {expected_types[suffix], "application/octet-stream"}:
        raise UnsupportedResumeTypeError("The file content type does not match its extension")
    return suffix


async def store_resume(candidate_id: str, upload: UploadFile) -> tuple[str, str]:
    original_name = Path(upload.filename or "").name
    suffix = validate_resume_type(original_name, upload.content_type)
    content = await upload.read(settings.max_resume_size + 1)
    if not content:
        raise EmptyResumeError("Resume file is empty")
    if len(content) > settings.max_resume_size:
        raise ResumeSizeError("Resume file exceeds the configured size limit")

    upload_directory = Path(settings.upload_directory).resolve()
    upload_directory.mkdir(parents=True, exist_ok=True)
    stored_name = f"{candidate_id}_{uuid.uuid4().hex}{suffix}"
    stored_path = upload_directory / stored_name
    try:
        stored_path.write_bytes(content)
    except OSError as exc:
        raise ResumeStorageError("Resume could not be stored") from exc
    return original_name, str(stored_path)


def extract_text(path: str) -> str:
    file_path = Path(path).resolve()
    if not file_path.is_file():
        raise ResumeError("Uploaded resume could not be found")

    try:
        if file_path.suffix.lower() == ".pdf":
            text = "\n".join(page.extract_text() or "" for page in PdfReader(str(file_path)).pages)
        elif file_path.suffix.lower() == ".docx":
            text = "\n".join(paragraph.text for paragraph in Document(str(file_path)).paragraphs)
        else:
            raise UnsupportedResumeTypeError("Only PDF and DOCX resumes are supported")
    except ResumeError:
        raise
    except Exception as exc:
        raise ResumeError("The uploaded resume is invalid or could not be read") from exc

    text = text.strip()
    if not text:
        raise EmptyResumeError("Resume contains no extractable text")
    return text


def _section(text: str, heading: str) -> str | None:
    match = re.search(rf"(?is)(?:^|\n){re.escape(heading)}\s*:?\s*(.*?)(?=\n[A-Z][A-Za-z &/]+\s*:?[ \t]*\n|$)", text)
    return match.group(1).strip() if match else None


def parse_resume_text(text: str):
    from app.modules.candidates.resume_schemas import ParsedResume

    email_match = re.search(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", text)
    phone_match = re.search(r"(?:\+?\d[\d ()-]{7,}\d)", text)
    skills_text = _section(text, "Skills")
    skills = [item.strip() for item in re.split(r",|\||;|\n", skills_text or "") if item.strip()]
    experience_match = re.search(r"(\d+)\+?\s+years?\s+(?:of\s+)?experience", text, re.I)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    name = lines[0] if lines and "@" not in lines[0] else None
    return ParsedResume(
        name=name,
        email=email_match.group(0) if email_match else None,
        phone=phone_match.group(0) if phone_match else None,
        skills=skills,
        education=_section(text, "Education"),
        experience_years=int(experience_match.group(1)) if experience_match else None,
        work_experience=[_section(text, "Experience")] if _section(text, "Experience") else [],
        certifications=[_section(text, "Certifications")] if _section(text, "Certifications") else [],
        projects=[_section(text, "Projects")] if _section(text, "Projects") else [],
        summary=_section(text, "Summary"),
    )