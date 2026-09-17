import json

import pytest
from pydantic import ValidationError

from app.content.loader import load_resume_source


def complete_resume() -> dict:
    return {
        "profile": {
            "id": "profile",
            "name": "Ada Example",
            "headline": "Engineer",
            "summary": "Builds useful systems.",
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
                "order": 1,
                "visibility": "published",
            }
        ],
        "education": [],
        "skills": [],
        "certifications": [],
        "contact_links": [],
    }


def write_resume(tmp_path, data: dict):
    path = tmp_path / "resume.json"
    path.write_text(json.dumps(data))
    return path


def test_loader_accepts_complete_resume_json(tmp_path):
    source = load_resume_source(write_resume(tmp_path, complete_resume()))

    assert source.profile.id == "profile"
    assert source.experience[0].end_date is None


def test_loader_rejects_unknown_visibility(tmp_path):
    data = complete_resume()
    data["profile"]["visibility"] = "public"

    with pytest.raises(ValidationError):
        load_resume_source(write_resume(tmp_path, data))


def test_loader_rejects_duplicate_ids_within_section(tmp_path):
    data = complete_resume()
    data["experience"].append({**data["experience"][0], "title": "Another"})

    with pytest.raises(ValidationError, match="duplicate id"):
        load_resume_source(write_resume(tmp_path, data))


def test_loader_rejects_invalid_date_ordering(tmp_path):
    data = complete_resume()
    data["experience"][0]["end_date"] = "2019-12"

    with pytest.raises(ValidationError, match="end_date"):
        load_resume_source(write_resume(tmp_path, data))


def test_loader_rejects_invalid_contact_link(tmp_path):
    data = complete_resume()
    data["contact_links"] = [
        {
            "id": "link-1",
            "label": "Website",
            "url": "not-a-url",
            "visibility": "published",
        }
    ]

    with pytest.raises(ValidationError, match="url"):
        load_resume_source(write_resume(tmp_path, data))
