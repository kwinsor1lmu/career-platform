# Task 7 report

## Status

Implemented Task 7 local Codespaces runtime and Azure operations documentation. The image runs as non-root `app`, persists only `./data` for local SQLite/fallback state, loads secrets/configuration from the environment, and excludes `.env`, databases, tests, docs, and local build artifacts from the image context. The checked-in `content/resume.json` remains the public seed source; private content is documented as a runtime-controlled input and is not intended for image builds.

## Commands and output

- Pre-container smoke sequence from the brief:
  - `cp .env.example .env` — completed.
  - `alembic upgrade head` — initially failed with `RuntimeError: DATABASE_URL is not set` because Alembic reads the process environment rather than Pydantic's `.env` file.
  - `python scripts/validate_content.py content/resume.json` — `Validated content/resume.json: profile and 2 experience, 1 education, 2 skill, 1 certification, and 1 contact link records.`
  - `python scripts/ingest_content.py content/resume.json` — `Ingested profile profile from content/resume.json and published fallback data/fallback.json: 2 experience, 1 education, 2 skills, 1 certifications, and 1 contact links.`
  - `timeout 8s uvicorn app.main:app --host 0.0.0.0 --port 8000` — startup completed and shutdown was clean after the timeout.
- `./scripts/dev.sh` smoke — migration, validation, ingestion, and Uvicorn startup all completed; timeout shutdown was clean. The script now exports `.env` before Alembic and supports an existing fallback when the source file is unavailable.
- `docker compose config` — succeeded and resolved the SQLite URL, port, healthcheck, and `./data:/app/data` bind mount.
- `timeout 90s docker compose up --build --abort-on-container-exit` — image built successfully after correcting the package-copy order; container migrated SQLite, validated/ingested the seed, started Uvicorn, and returned `GET /health` 200. The command timed out as expected because the web service is long-running.
- Container endpoint checks:
  - `curl --fail http://127.0.0.1:8000/health` — `{"status":"ok"}`.
  - `curl --fail http://127.0.0.1:8000/` — rendered the title and `Experience`, `Education`, `Skills`, and `Contact` sections.
  - `docker compose exec -T app id` — `uid=999(app) gid=999(app) groups=999(app)`.
  - `docker compose down` — completed successfully.
- `pytest -q` — `23 passed, 1 warning`.
- `git diff --check` — no whitespace errors.

## Concerns

- The first health curl immediately after `docker compose up -d` raced the migration/ingest startup and received `connection reset by peer`; a retry after startup returned 200. The documented healthcheck has a start period, and callers should wait for readiness rather than assume the port is ready immediately.
- The existing Starlette/httpx deprecation warning remains during tests; it is unrelated to Task 7.
- Azure infrastructure is intentionally not provisioned here. The operations document records PostgreSQL, HTTPS/reverse-proxy, firewall, backup/restore, migration ordering, and health-check assumptions for a later deployment.
