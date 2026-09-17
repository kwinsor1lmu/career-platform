from sqlalchemy import create_engine, inspect

from app.models import Base


def test_initial_schema_contains_resume_sections():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    tables = set(inspect(engine).get_table_names())

    assert {"profiles", "experiences", "educations", "skills", "certifications", "contact_links"} <= tables
