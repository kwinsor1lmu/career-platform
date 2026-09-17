from pathlib import Path

from app.schemas import ResumeSource


def load_resume_source(path: Path) -> ResumeSource:
    return ResumeSource.model_validate_json(path.read_text(encoding="utf-8"))
