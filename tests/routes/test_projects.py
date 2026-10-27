from fastapi.testclient import TestClient

from app.main import create_app
from app.repositories.resume import PublicResume
from app.schemas import Profile, Project


def _resume() -> PublicResume:
    return PublicResume(
        profile=Profile(
            id="profile",
            name="Ada Example",
            headline="Software engineer",
            summary="Builds useful systems.",
            visibility="published",
        )
    )


def _project() -> Project:
    return Project(
        id="this-site",
        name="This resume site",
        status="In progress",
        summary="A site that reads its projects from a database.",
        url="https://github.com/example/career-platform",
        order=1,
        visibility="published",
    )


def _get(monkeypatch, projects, source: str = "database"):
    monkeypatch.setattr(
        "app.routes.resume.load_resume_with_fallback",
        lambda session_factory, fallback_path: (_resume(), source),
    )
    monkeypatch.setattr("app.routes.resume.load_public_projects", lambda session_factory: projects)
    return TestClient(create_app()).get("/")


def test_projects_from_database_are_listed(monkeypatch):
    response = _get(monkeypatch, [_project()])

    assert response.status_code == 200
    assert 'id="projects"' in response.text
    assert "This resume site" in response.text
    assert "In progress" in response.text
    assert 'href="https://github.com/example/career-platform"' in response.text


def test_empty_projects_table_says_so_with_200(monkeypatch):
    response = _get(monkeypatch, [])

    assert response.status_code == 200
    assert "No projects listed yet." in response.text
    assert "temporarily unavailable" not in response.text


def test_unavailable_projects_return_503_and_keep_profile(monkeypatch):
    response = _get(monkeypatch, None, source="fallback")

    assert response.status_code == 503
    assert "Projects temporarily unavailable" in response.text
    assert "Ada Example" in response.text
    assert "This resume site" not in response.text
