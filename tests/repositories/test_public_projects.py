from app.content.ingest import ingest_resume
from app.repositories.resume import get_public_projects
from app.schemas import ResumeSource


def _source(projects: list[dict]) -> ResumeSource:
    return ResumeSource.model_validate(
        {
            "profile": {
                "id": "profile",
                "name": "Ada Example",
                "headline": "Software engineer",
                "summary": "Public summary.",
                "visibility": "published",
            },
            "projects": projects,
        }
    )


def test_public_projects_are_read_from_the_database_in_order(session):
    ingest_resume(
        session,
        _source(
            [
                {"id": "second", "name": "Second", "summary": "Two.", "order": 2, "visibility": "published"},
                {"id": "hidden", "name": "Hidden", "summary": "private fixture text", "order": 0, "visibility": "private"},
                {
                    "id": "first",
                    "name": "First",
                    "status": "In progress",
                    "summary": "One.",
                    "url": "https://example.com/first",
                    "order": 1,
                    "visibility": "published",
                },
            ]
        ),
    )

    projects = get_public_projects(session)

    assert [project.id for project in projects] == ["first", "second"]
    assert projects[0].status == "In progress"
    assert str(projects[0].url) == "https://example.com/first"


def test_public_projects_empty_table_returns_empty_list(session):
    ingest_resume(session, _source([]))

    assert get_public_projects(session) == []


def test_reingest_removes_deleted_projects(session):
    ingest_resume(session, _source([{"id": "old", "name": "Old", "summary": "Old.", "order": 1, "visibility": "published"}]))
    ingest_resume(session, _source([{"id": "new", "name": "New", "summary": "New.", "order": 1, "visibility": "published"}]))

    assert [project.id for project in get_public_projects(session)] == ["new"]
