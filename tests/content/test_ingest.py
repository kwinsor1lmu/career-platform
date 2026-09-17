from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.content.ingest import ingest_resume
from app.models import Base
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


def count_rows(session: Session, model_name: str) -> int:
    mapping = {
        "profiles": __import__("app.models", fromlist=["Profile"]).Profile,
        "experiences": __import__("app.models", fromlist=["Experience"]).Experience,
        "educations": __import__("app.models", fromlist=["Education"]).Education,
        "skills": __import__("app.models", fromlist=["Skill"]).Skill,
        "certifications": __import__("app.models", fromlist=["Certification"]).Certification,
        "contact_links": __import__("app.models", fromlist=["ContactLink"]).ContactLink,
    }
    return session.query(mapping[model_name]).count()


def test_ingestion_is_repeatable(session: Session, source: ResumeSource):
    ingest_resume(session, source)
    ingest_resume(session, source)

    assert count_rows(session, "experiences") == len(source.experience)
    assert count_rows(session, "skills") == len(source.skills)
    assert count_rows(session, "contact_links") == len(source.contact_links)


def test_ingestion_updates_existing_rows_without_duplicates(session: Session, source: ResumeSource):
    ingest_resume(session, source)

    updated = source.model_copy(deep=True)
    updated.experience[0].summary = "Updated description"
    updated.experience[0].visibility = "private"

    ingest_resume(session, updated)

    assert count_rows(session, "experiences") == len(updated.experience)
    row = session.query(__import__("app.models", fromlist=["Experience"]).Experience).filter_by(stable_id="example-co-engineer").one()
    assert row.summary == "Updated description"
    assert row.visibility == "private"
