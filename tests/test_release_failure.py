import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy.exc import OperationalError

from app.config import Settings
from app.content.fallback import load_public_fallback
from app.schemas import ResumeSource

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "ingest_content.py"


def _load_release_module():
    spec = importlib.util.spec_from_file_location("release_ingest", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_release_fails_on_malformed_source(tmp_path):
    bad_source = tmp_path / "malformed.json"
    bad_source.write_text('{"profile":', encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(bad_source)],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "Ingestion failed" in result.stderr
    assert "invalid JSON" in result.stderr
    assert "Traceback" not in result.stderr


def test_release_fails_when_production_database_is_missing():
    with pytest.raises(ValueError, match="DATABASE_URL must point to PostgreSQL in production"):
        Settings(environment="production", database_url="sqlite:///./data/app.db")


def test_release_fails_on_invalid_fallback(tmp_path):
    fallback_path = tmp_path / "fallback.json"
    fallback_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "generated_at": "2024-01-01T00:00:00+00:00",
                "resume": {
                    "profile": {
                        "id": "profile",
                        "name": "Ada Example",
                        "headline": "Software engineer",
                        "summary": "Public summary.",
                        "visibility": "private",
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        load_public_fallback(fallback_path)


def test_release_fails_when_migration_or_release_step_errors(tmp_path):
    module = _load_release_module()
    release_resume = module.release_resume
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
    fallback_path = tmp_path / "fallback.json"

    class FailingSession:
        def begin(self):
            raise OperationalError("migration failed", {}, RuntimeError("migration failed"))

        def rollback(self):
            return None

    with pytest.raises(OperationalError, match="migration failed"):
        release_resume(FailingSession(), source, fallback_path)
