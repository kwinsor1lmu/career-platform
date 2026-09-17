from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.models import Base
from app.repositories.resume import PublicResume
from app.schemas import ResumeSource


@pytest.fixture
def session() -> Session:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    with session_local() as db_session:
        yield db_session


@pytest.fixture
def source() -> ResumeSource:
    return ResumeSource.model_validate(
        {
            "profile": {
                "id": "profile",
                "name": "Ada Example",
                "headline": "Software engineer",
                "summary": "Public summary.",
                "visibility": "published",
            },
            "experience": [
                {
                    "id": "published-work",
                    "employer": "Example Co",
                    "title": "Engineer",
                    "summary": "Public work.",
                    "order": 1,
                    "visibility": "published",
                },
                {
                    "id": "private-work",
                    "employer": "Private Co",
                    "title": "Lead",
                    "summary": "Private work.",
                    "order": 2,
                    "visibility": "private",
                },
            ],
        }
    )


@pytest.fixture
def public_resume() -> PublicResume:
    source = ResumeSource.model_validate(
        {
            "profile": {
                "id": "profile",
                "name": "Ada Example",
                "headline": "Software engineer",
                "summary": "Public summary.",
                "visibility": "published",
            }
        }
    )
    return PublicResume(profile=source.profile)
