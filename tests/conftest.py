from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker

from app.config import Settings
from app.content.fallback import write_public_fallback
from app.main import create_app
from app.models import Base
from app.repositories.resume import PublicResume
from app.schemas import ContactLink, Profile, ResumeSource


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
                    "summary": "private fixture text",
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
            },
            "contact_links": [
                {
                    "id": "portfolio",
                    "label": "Portfolio",
                    "url": "https://example.com",
                    "order": 0,
                    "visibility": "published",
                }
            ],
        }
    )
    return PublicResume(
        profile=source.profile,
        contact_links=source.contact_links,
    )


@pytest.fixture
def app_client(tmp_path, monkeypatch):
    fallback_path = tmp_path / "fallback.json"
    public_resume = PublicResume(
        profile=Profile(
            id="profile",
            name="Ada Example",
            headline="Software engineer",
            summary="Public summary.",
            visibility="published",
        ),
        contact_links=[
            ContactLink(
                id="portfolio",
                label="Portfolio",
                url="https://example.com",
                order=0,
                visibility="published",
            )
        ],
    )
    write_public_fallback(public_resume, fallback_path)

    def fail_session_factory():
        raise OperationalError("database unavailable", {}, ConnectionError("offline"))

    monkeypatch.setattr("app.routes.resume.SessionLocal", fail_session_factory)
    app = create_app(Settings(environment="test", database_url="sqlite://", fallback_path=fallback_path))
    with TestClient(app) as client:
        yield client


@pytest.fixture
def outage_client(tmp_path, monkeypatch):
    fallback_path = tmp_path / "fallback.json"
    public_resume = PublicResume(
        profile=Profile(
            id="profile",
            name="Ada Example",
            headline="Software engineer",
            summary="Public summary.",
            visibility="published",
        ),
        contact_links=[
            ContactLink(
                id="portfolio",
                label="Portfolio",
                url="https://example.com",
                order=0,
                visibility="published",
            )
        ],
    )
    write_public_fallback(public_resume, fallback_path)

    def fail_session_factory():
        raise OperationalError("database unavailable", {}, ConnectionError("offline"))

    monkeypatch.setattr("app.routes.resume.SessionLocal", fail_session_factory)
    app = create_app(Settings(environment="test", database_url="sqlite://", fallback_path=fallback_path))
    with TestClient(app) as client:
        yield client
