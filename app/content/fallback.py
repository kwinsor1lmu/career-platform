from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from app.repositories.resume import PublicResume
from app.schemas import ResumeSource

FALLBACK_SCHEMA_VERSION = 1


def _resume_payload(resume: PublicResume) -> dict[str, Any]:
    if resume.profile.visibility != "published":
        raise ValueError("fallback profile must be published")
    if any(item.visibility != "published" for item in resume.all_items()):
        raise ValueError("fallback items must be published")
    return {
        "profile": resume.profile.model_dump(mode="json"),
        "experience": [item.model_dump(mode="json") for item in resume.experience],
        "education": [item.model_dump(mode="json") for item in resume.education],
        "skills": [item.model_dump(mode="json") for item in resume.skills],
        "certifications": [item.model_dump(mode="json") for item in resume.certifications],
        "contact_links": [item.model_dump(mode="json") for item in resume.contact_links],
    }


def write_public_fallback(resume: PublicResume, path: Path) -> None:
    payload = {
        "schema_version": FALLBACK_SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "resume": _resume_payload(resume),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as temporary:
            temporary.write(encoded)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_name, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except BaseException:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def load_public_fallback(path: Path) -> PublicResume:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or raw.get("schema_version") != FALLBACK_SCHEMA_VERSION:
        raise ValueError("unsupported fallback schema version")
    if not isinstance(raw.get("generated_at"), str) or not isinstance(raw.get("resume"), dict):
        raise ValueError("invalid fallback envelope")
    try:
        datetime.fromisoformat(raw["generated_at"])
    except ValueError as error:
        raise ValueError("invalid fallback generation timestamp") from error
    try:
        source = ResumeSource.model_validate(raw["resume"])
    except ValidationError as error:
        raise ValueError("invalid public fallback content") from error
    if source.profile.visibility != "published" or any(
        item.visibility != "published" for item in source.experience + source.education + source.skills + source.certifications + source.contact_links
    ):
        raise ValueError("fallback contains non-public content")
    return PublicResume(
        profile=source.profile,
        experience=source.experience,
        education=source.education,
        skills=source.skills,
        certifications=source.certifications,
        contact_links=source.contact_links,
    )
