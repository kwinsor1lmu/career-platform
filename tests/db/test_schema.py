import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError

from app.models import Base


def test_initial_schema_contains_resume_sections():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    tables = set(inspect(engine).get_table_names())

    assert {"profiles", "experiences", "educations", "skills", "certifications", "contact_links"} <= tables


def test_composite_profile_owner_boundary_is_enforced():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)

    with engine.begin() as conn:
        conn.execute(text("PRAGMA foreign_keys = ON"))
        conn.execute(
            text(
                "INSERT INTO profiles (id, owner_id, name, headline, summary, visibility) "
                "VALUES (:id, :owner_id, :name, :headline, :summary, :visibility)"
            ),
            {
                "id": "profile-1",
                "owner_id": "owner-1",
                "name": "Ada",
                "headline": "Engineer",
                "summary": "Builds useful systems.",
                "visibility": "published",
            },
        )
        conn.execute(
            text(
                "INSERT INTO experiences (profile_id, owner_id, stable_id, visibility, display_order, "
                "created_at, updated_at, employer, title, summary, start_date, end_date) "
                "VALUES (:profile_id, :owner_id, :stable_id, :visibility, :display_order, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, :employer, :title, :summary, :start_date, :end_date)"
            ),
            {
                "profile_id": "profile-1",
                "owner_id": "owner-1",
                "stable_id": "exp-1",
                "visibility": "published",
                "display_order": 1,
                "employer": "Example Co",
                "title": "Engineer",
                "summary": "Built systems.",
                "start_date": "2020-01",
                "end_date": None,
            },
        )

        with pytest.raises(IntegrityError):
            conn.execute(
                text(
                    "INSERT INTO experiences (profile_id, owner_id, stable_id, visibility, display_order, "
                    "created_at, updated_at, employer, title, summary, start_date, end_date) "
                    "VALUES (:profile_id, :owner_id, :stable_id, :visibility, :display_order, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, :employer, :title, :summary, :start_date, :end_date)"
                ),
                {
                    "profile_id": "profile-1",
                    "owner_id": "owner-2",
                    "stable_id": "exp-2",
                    "visibility": "published",
                    "display_order": 2,
                    "employer": "Other Firm",
                    "title": "Engineer",
                    "summary": "Different systems.",
                    "start_date": "2021-01",
                    "end_date": None,
                },
            )
