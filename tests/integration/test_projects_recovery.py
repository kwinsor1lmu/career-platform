from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import Settings
from app.content.fallback import write_public_fallback
from app.content.ingest import ingest_resume
from app.main import create_app
from app.models import Base
from app.repositories.resume import get_public_resume
from app.schemas import ResumeSource


def _source() -> ResumeSource:
    return ResumeSource.model_validate(
        {
            "profile": {
                "id": "profile",
                "name": "Ada Example",
                "headline": "Software engineer",
                "summary": "Public summary.",
                "visibility": "published",
            },
            "projects": [
                {
                    "id": "this-site",
                    "name": "This resume site",
                    "summary": "Reads projects from the database.",
                    "order": 1,
                    "visibility": "published",
                }
            ],
        }
    )


def test_projects_return_after_database_recovers_without_restart(tmp_path, monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session_local = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with session_local() as session:
        ingest_resume(session, _source())
        fallback_path = tmp_path / "fallback.json"
        write_public_fallback(get_public_resume(session), fallback_path)

    database_up = {"value": False}

    def session_factory():
        if not database_up["value"]:
            raise OperationalError("database unavailable", {}, ConnectionError("offline"))
        return session_local()

    monkeypatch.setattr("app.routes.resume.SessionLocal", session_factory)
    app = create_app(Settings(environment="test", database_url="sqlite://", fallback_path=fallback_path))

    with TestClient(app) as client:
        down = client.get("/")
        assert down.status_code == 503
        assert "Projects temporarily unavailable" in down.text
        assert "This resume site" not in down.text

        database_up["value"] = True
        up = client.get("/")
        assert up.status_code == 200
        assert "This resume site" in up.text
        assert "temporarily unavailable" not in up.text
