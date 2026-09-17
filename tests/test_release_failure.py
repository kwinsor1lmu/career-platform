import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "ingest_content.py"


def _valid_source(path: Path) -> Path:
    payload = {
        "profile": {
            "id": "profile",
            "name": "Ada Example",
            "headline": "Software engineer",
            "summary": "Public summary.",
            "visibility": "published",
        },
        "experience": [
            {
                "id": "exp-1",
                "employer": "Example Co",
                "title": "Engineer",
                "start_date": "2020-01",
                "end_date": None,
                "summary": "Built systems.",
                "order": 0,
                "visibility": "published",
            }
        ],
        "education": [],
        "skills": [],
        "certifications": [],
        "contact_links": [],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _valid_fallback(path: Path) -> str:
    payload = {
        "schema_version": 1,
        "generated_at": "2024-01-01T00:00:00+00:00",
        "resume": {
            "profile": {
                "id": "profile",
                "name": "Ada Example",
                "headline": "Software engineer",
                "summary": "Public summary.",
                "visibility": "published",
            },
            "experience": [],
            "education": [],
            "skills": [],
            "certifications": [],
            "contact_links": [],
        },
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path.read_text(encoding="utf-8")


def _run_ingest(source_path: Path, *, fallback_path: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    command_env = os.environ.copy()
    if env:
        command_env.update(env)
    command_env.setdefault("ENVIRONMENT", "development")
    command_env.setdefault("DATABASE_URL", "sqlite:///./data/app.db")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(source_path), "--fallback", str(fallback_path)],
        capture_output=True,
        text=True,
        env=command_env,
        cwd=str(ROOT),
    )
    return result


def test_release_fails_on_malformed_source_and_keeps_previous_fallback(tmp_path):
    source_path = tmp_path / "malformed.json"
    source_path.write_text('{"profile":', encoding="utf-8")
    fallback_path = tmp_path / "fallback.json"
    original = _valid_fallback(fallback_path)

    result = _run_ingest(source_path, fallback_path=fallback_path)

    assert result.returncode != 0
    assert "Ingestion failed" in result.stderr
    assert "invalid JSON" in result.stderr
    assert "Traceback" not in result.stderr
    assert fallback_path.read_text(encoding="utf-8") == original


def test_release_fails_on_missing_production_config_and_keeps_previous_fallback(tmp_path):
    source_path = _valid_source(tmp_path / "resume.json")
    fallback_path = tmp_path / "fallback.json"
    original = _valid_fallback(fallback_path)

    result = _run_ingest(
        source_path,
        fallback_path=fallback_path,
        env={"ENVIRONMENT": "production", "DATABASE_URL": "sqlite:///./data/app.db"},
    )

    assert result.returncode != 0
    assert "invalid configuration" in result.stderr.lower()
    assert "postgresql" in result.stderr.lower()
    assert fallback_path.read_text(encoding="utf-8") == original


def test_release_fails_on_invalid_fallback_and_keeps_target_bytes_unchanged(tmp_path):
    source_path = _valid_source(tmp_path / "resume.json")
    fallback_path = tmp_path / "fallback.json"
    previous_bytes = _valid_fallback(fallback_path).encode("utf-8")
    invalid_bytes = b'{"schema_version": 1, "generated_at": "bad"}'
    fallback_path.write_bytes(invalid_bytes)

    result = _run_ingest(source_path, fallback_path=fallback_path)

    assert result.returncode != 0
    assert "invalid fallback" in result.stderr.lower()
    assert "Traceback" not in result.stderr
    assert fallback_path.read_bytes() == invalid_bytes
    assert fallback_path.read_bytes() != previous_bytes


def test_release_fails_when_database_connection_fails_during_release_step_and_keeps_previous_fallback(tmp_path):
    source_path = _valid_source(tmp_path / "resume.json")
    fallback_path = tmp_path / "fallback.json"
    original = _valid_fallback(fallback_path)

    result = _run_ingest(
        source_path,
        fallback_path=fallback_path,
        env={
            "ENVIRONMENT": "production",
            "DATABASE_URL": "postgresql+psycopg://user:pass@127.0.0.1:1/does-not-exist",
        },
    )

    assert result.returncode != 0
    assert "Ingestion failed" in result.stderr
    assert "database" in result.stderr.lower() or "connection" in result.stderr.lower()
    assert "Traceback" not in result.stderr
    assert fallback_path.read_text(encoding="utf-8") == original
