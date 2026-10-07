import pytest

from app.config import Settings


@pytest.fixture(autouse=True)
def clean_settings_env(monkeypatch):
    # A shell exported for a production rehearsal must not change what these tests see.
    for name in ("ENVIRONMENT", "DATABASE_URL"):
        monkeypatch.delenv(name, raising=False)


def test_plain_postgresql_url_uses_psycopg_driver():
    settings = Settings(_env_file=None, database_url="postgresql://user:pw@postgres.railway.internal:5432/railway")

    assert settings.database_url == "postgresql+psycopg://user:pw@postgres.railway.internal:5432/railway"


def test_explicit_psycopg_url_is_unchanged():
    url = "postgresql+psycopg://user:pw@localhost:5432/app"

    assert Settings(_env_file=None, database_url=url).database_url == url


def test_sqlite_url_is_unchanged():
    url = "sqlite:///./data/app.db"

    assert Settings(_env_file=None, database_url=url).database_url == url


def test_production_accepts_railway_postgres_url():
    settings = Settings(
        _env_file=None,
        environment="production",
        database_url="postgresql://user:pw@postgres.railway.internal:5432/railway",
    )

    assert settings.database_url.startswith("postgresql+psycopg://")


def test_production_still_rejects_sqlite():
    with pytest.raises(ValueError, match="PostgreSQL in production"):
        Settings(_env_file=None, environment="production", database_url="sqlite:///./data/app.db")
