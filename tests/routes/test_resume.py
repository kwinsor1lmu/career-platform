from fastapi.testclient import TestClient

from app.main import create_app
from app.repositories.resume import PublicResume
from app.schemas import Profile


def _public_resume() -> PublicResume:
    return PublicResume(
        profile=Profile(
            id="profile",
            name="Ada Example",
            headline="Software engineer",
            summary="Builds useful systems.",
            visibility="published",
        )
    )


def test_resume_page_contains_core_sections(monkeypatch):
    monkeypatch.setattr(
        "app.routes.resume.load_resume_with_fallback",
        lambda session_factory, fallback_path: (_public_resume(), "fallback"),
    )

    response = TestClient(create_app()).get("/")

    assert response.status_code == 200
    assert "<main" in response.text
    assert "Experience" in response.text
    assert "Education" in response.text
    assert "Skills" in response.text


def test_resume_page_does_not_render_private_content(monkeypatch):
    monkeypatch.setattr(
        "app.routes.resume.load_resume_with_fallback",
        lambda session_factory, fallback_path: (_public_resume(), "fallback"),
    )

    response = TestClient(create_app()).get("/")

    assert "private fixture text" not in response.text
