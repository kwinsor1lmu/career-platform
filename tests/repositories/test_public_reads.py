from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.content.ingest import ingest_resume
from app.models import Base
from app.repositories.resume import get_public_resume
from app.schemas import ResumeSource


@pytest.fixture
def session() -> Session:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    with SessionLocal() as db_session:
        yield db_session


@pytest.fixture
def source() -> ResumeSource:
    return ResumeSource.model_validate(
        {
            "profile": {
                "id": "profile",
                "name": "Ada Example",
                "headline": "Software engineer building useful systems",
                "summary": "Example content for the personal resume platform.",
                "visibility": "published",
            },
            "experience": [
                {
                    "id": "example-co-engineer",
                    "employer": "Example Co",
                    "title": "Software Engineer",
                    "start_date": "2020-01",
                    "end_date": None,
                    "summary": "Built reliable systems and documented the work.",
                    "order": 1,
                    "visibility": "published",
                },
                {
                    "id": "private-project",
                    "employer": "Private Example Project",
                    "title": "Technical Lead",
                    "start_date": "2019",
                    "end_date": "2019-12",
                    "summary": "Draft record reserved for future publication.",
                    "order": 2,
                    "visibility": "private",
                },
            ],
            "education": [
                {
                    "id": "example-university",
                    "institution": "Example University",
                    "degree": "BSc Computer Science",
                    "start_date": "2016-09",
                    "end_date": "2020-06",
                    "summary": "Example academic history.",
                    "order": 1,
                    "visibility": "published",
                }
            ],
            "skills": [
                {
                    "id": "python",
                    "name": "Python",
                    "level": "Advanced",
                    "order": 1,
                    "visibility": "published",
                },
                {
                    "id": "prototype-skill",
                    "name": "Unpublished skill",
                    "level": "Draft",
                    "order": 2,
                    "visibility": "draft",
                },
            ],
            "certifications": [
                {
                    "id": "example-certification",
                    "name": "Example Cloud Certificate",
                    "issuer": "Example Institute",
                    "start_date": "2023",
                    "end_date": None,
                    "summary": "Representative certification record.",
                    "order": 1,
                    "visibility": "published",
                }
            ],
            "contact_links": [
                {
                    "id": "github",
                    "label": "GitHub",
                    "url": "https://github.com/example",
                    "order": 1,
                    "visibility": "published",
                }
            ],
        }
    )


def test_public_read_excludes_drafts_and_private_records(session: Session, source: ResumeSource):
    ingest_resume(session, source)

    public = get_public_resume(session)

    assert public.profile.visibility == "published"
    assert all(item.visibility == "published" for item in public.all_items())
    assert all(item.id != "private-project" for item in public.all_items())
    assert all(item.id != "prototype-skill" for item in public.all_items())
