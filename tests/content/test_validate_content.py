import json
import subprocess
import sys

from tests.content.test_loader import complete_resume


SCRIPT = "scripts/validate_content.py"


def run_cli(path):
    return subprocess.run(
        [sys.executable, SCRIPT, str(path)],
        capture_output=True,
        text=True,
    )


def test_cli_reports_malformed_json(tmp_path):
    path = tmp_path / "malformed.json"
    path.write_text("{\"profile\":", encoding="utf-8")

    result = run_cli(path)

    assert result.returncode != 0
    assert str(path) in result.stderr
    assert "invalid JSON" in result.stderr
    assert "Traceback" not in result.stderr


def test_cli_reports_invalid_utf8(tmp_path):
    path = tmp_path / "invalid-utf8.json"
    path.write_bytes(b"{\xff")

    result = run_cli(path)

    assert result.returncode != 0
    assert str(path) in result.stderr
    assert "unable to read" in result.stderr
    assert "UTF-8" in result.stderr
    assert "Traceback" not in result.stderr


def test_cli_reports_missing_path(tmp_path):
    path = tmp_path / "missing.json"

    result = run_cli(path)

    assert result.returncode != 0
    assert str(path) in result.stderr
    assert "file not found" in result.stderr
    assert "Traceback" not in result.stderr


def test_cli_reports_unreadable_path(tmp_path):
    path = tmp_path / "directory"
    path.mkdir()

    result = run_cli(path)

    assert result.returncode != 0
    assert str(path) in result.stderr
    assert "unable to read" in result.stderr
    assert "Traceback" not in result.stderr
