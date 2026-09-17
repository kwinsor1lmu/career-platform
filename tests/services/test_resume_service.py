from pathlib import Path
from types import SimpleNamespace

from sqlalchemy.exc import OperationalError

from app.content.fallback import write_public_fallback
from app.services.resume import load_resume_with_fallback


def test_service_uses_database_first(tmp_path: Path, public_resume, monkeypatch):
    path = tmp_path / "fallback.json"
    write_public_fallback(public_resume, path)

    monkeypatch.setattr("app.services.resume.get_public_resume", lambda session: public_resume)
    result, source = load_resume_with_fallback(lambda: SimpleNamespace(close=lambda: None), path)

    assert source == "database"
    assert result.profile.id == public_resume.profile.id


def test_service_uses_fallback_when_database_is_unavailable(tmp_path: Path, public_resume):
    path = tmp_path / "fallback.json"
    write_public_fallback(public_resume, path)

    def raise_database_error():
        raise OperationalError("database unavailable", {}, ConnectionError("offline"))

    result, source = load_resume_with_fallback(raise_database_error, path)

    assert source == "fallback"
    assert result.profile.id == public_resume.profile.id


def test_service_uses_fallback_when_database_has_no_published_profile(tmp_path: Path, public_resume, monkeypatch):
    path = tmp_path / "fallback.json"
    write_public_fallback(public_resume, path)

    def raise_no_published_profile(session):
        raise ValueError("No published profile is available for this owner.")

    monkeypatch.setattr("app.services.resume.get_public_resume", raise_no_published_profile)
    result, source = load_resume_with_fallback(lambda: SimpleNamespace(close=lambda: None), path)

    assert source == "fallback"
    assert result.profile.id == public_resume.profile.id
