from pathlib import Path

from app.content.fallback import load_public_fallback, write_public_fallback
from app.content.ingest import ingest_resume
from app.repositories.resume import get_public_resume


def test_fallback_contains_only_published_public_content(tmp_path: Path, source, session):
    ingest_resume(session, source)
    path = tmp_path / "fallback.json"

    write_public_fallback(get_public_resume(session), path)
    fallback = load_public_fallback(path)

    assert all(item.visibility == "published" for item in fallback.all_items())
    assert all(item.id not in {"private-project", "prototype-skill"} for item in fallback.all_items())


def test_fallback_write_is_atomic_on_serialization_failure(tmp_path: Path, public_resume):
    path = tmp_path / "fallback.json"
    write_public_fallback(public_resume, path)
    previous = path.read_bytes()

    public_resume.profile.visibility = "private"
    try:
        write_public_fallback(public_resume, path)
    except ValueError:
        pass

    assert path.read_bytes() == previous
