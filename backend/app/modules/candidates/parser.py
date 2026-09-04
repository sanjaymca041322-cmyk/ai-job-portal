from typing import Protocol

from app.core.config import settings
from app.modules.candidates.resume_schemas import ParsedResume
from app.modules.candidates.resume_service import parse_resume_text


class ResumeParserProvider(Protocol):
    def parse(self, text: str) -> ParsedResume:
        ...


class FallbackResumeParser:
    def parse(self, text: str) -> ParsedResume:
        return parse_resume_text(text)


class ResumeParser:
    def __init__(self, provider: ResumeParserProvider | None = None) -> None:
        self.provider = provider or FallbackResumeParser()

    def parse(self, text: str) -> ParsedResume:
        if settings.llm_api_key and settings.llm_provider != "fallback":
            return self.provider.parse(text)
        return FallbackResumeParser().parse(text)