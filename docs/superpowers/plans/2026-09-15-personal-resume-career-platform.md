# Personal Resume and Career Platform Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local-first, database-backed public resume site with Git-managed JSON content, a database-independent fallback, and a migration path from SQLite in Codespaces to PostgreSQL on an Azure VM.

**Architecture:** FastAPI serves Jinja-rendered pages with plain CSS. A typed domain layer validates JSON source content, persists normalized records through SQLAlchemy, and exposes a single public read model that enforces published visibility and ordering. The build produces a public fallback snapshot from validated content; runtime reads prefer the database and fall back to that snapshot when the database is unavailable.

**Tech Stack:** Python 3, FastAPI, Uvicorn, Jinja2, SQLAlchemy 2, Alembic, Pydantic 2, SQLite locally, PostgreSQL on the eventual Azure VM, pytest, plain CSS, and JSON source content.

**Spec:** `docs/superpowers/specs/2026-09-15-personal-resume-career-platform-design.md`

## Global Constraints

- The first release is single-user and focused on the core resume; do not build a browser-based admin editor.
- Resume content is authored in version-controlled files and published through Git and deployment.
- Public responses include only records with the published public state; drafts and private records never enter HTML, metadata, API responses, bundles, or search results.
- Records use stable identifiers and explicit ordering; date ranges support incomplete dates and “present.”
- The public profile must remain available when the database is unavailable by serving the latest validated public fallback.
- Invalid content, failed ingestion, missing configuration, and database failures must surface actionable diagnostics rather than silent success-shaped fallbacks.
- No secrets or private source content may be committed.
- Core resume access must not require client-side JavaScript.
- Public pages must use semantic HTML, responsive layout, keyboard access, visible focus, readable contrast, and meaningful metadata.
- Local development uses SQLite; the eventual Azure VM deployment uses PostgreSQL with the same domain interfaces.
- The plan assumes a minimal, content-first visual direction: readable typography, restrained spacing/color, and no custom brand system until a later design task.

---

## File and module map

The implementation should keep responsibilities separate:

- `pyproject.toml`: Python dependencies, tool configuration, and test commands.
- `app/main.py`: FastAPI application factory and route registration.
- `app/config.py`: typed environment configuration.
- `app/db.py`: SQLAlchemy engine, session factory, and lifecycle helpers.
- `app/models.py`: persistence models and visibility/order fields.
- `app/schemas.py`: Pydantic source-content and public-view schemas.
- `app/content/loader.py`: JSON loading and source validation.
- `app/content/ingest.py`: idempotent source-to-database ingestion.
- `app/content/fallback.py`: public-only fallback snapshot generation and loading.
- `app/repositories/resume.py`: centralized public and owner-scoped reads.
- `app/services/resume.py`: database-first/fallback resume assembly.
- `app/templates/base.html`, `app/templates/resume.html`: semantic page templates.
- `app/static/styles.css`: responsive plain-CSS presentation.
- `content/resume.json`: seeded public and private example content.
- `scripts/validate_content.py`, `scripts/ingest_content.py`: explicit release commands.
- `alembic/`: repeatable schema migrations.
- `tests/`: focused unit, integration, route, fallback, and accessibility-oriented checks.
- `Dockerfile`, `docker-compose.yml`, `.env.example`: reproducible local runtime.
- `docs/operations/local-and-azure.md`: Codespaces and Azure VM deployment/runbook.

### Task 1: Establish the Python application foundation

**Files:**
- Create: `pyproject.toml`
- Create: `app/__init__.py`
- Create: `app/main.py`
- Create: `app/config.py`
- Create: `tests/test_health.py`
- Create: `.env.example`

**Interfaces:**
- Produces `create_app() -> FastAPI` from `app.main`.
- Produces `Settings` from `app.config`, with `environment`, `database_url`, `content_path`, and `fallback_path`.
- Produces `GET /health` returning a small JSON health result without querying private content.

- [ ] **Step 1: Write the failing health test**

```python
from fastapi.testclient import TestClient

from app.main import create_app


def test_health_endpoint_reports_application_health():
    response = TestClient(create_app()).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 2: Run the focused test and verify it fails**

Run: `pytest tests/test_health.py -q`

Expected: FAIL because the application package and `create_app` do not exist yet.

- [ ] **Step 3: Add the minimal application and configuration**

Define the dependencies and `create_app()` factory. Read configuration from environment variables with explicit defaults for local development; reject malformed URLs or missing required production settings rather than silently substituting values.

- [ ] **Step 4: Run the focused test and verify it passes**

Run: `pytest tests/test_health.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml app tests/test_health.py .env.example
git commit -m "feat: establish FastAPI application foundation"
```

**Done looks like:** A fresh Codespaces checkout can install the declared dependencies and start a FastAPI app whose health endpoint passes without requiring a database.

**How to check:** Run `python -m pytest tests/test_health.py -q` and `uvicorn app.main:create_app --factory --reload`; request `http://127.0.0.1:8000/health` and confirm `{"status":"ok"}`.

### Task 2: Define the typed resume content contract

**Files:**
- Create: `app/schemas.py`
- Create: `app/content/loader.py`
- Create: `content/resume.json`
- Create: `tests/content/test_loader.py`
- Create: `scripts/validate_content.py`

**Interfaces:**
- Produces `ResumeSource.model_validate_json(text) -> ResumeSource`.
- Produces `load_resume_source(path: Path) -> ResumeSource`.
- Produces `Visibility = Literal["draft", "private", "published"]`.
- Produces `scripts/validate_content.py` as a nonzero-exit validation command.

- [ ] **Step 1: Write failing validation tests**

```python
import json

import pytest
from pydantic import ValidationError

from app.content.loader import load_resume_source


def test_loader_accepts_complete_resume_json(tmp_path):
    path = tmp_path / "resume.json"
    path.write_text(json.dumps({
        "profile": {"id": "profile", "name": "Ada Example", "headline": "Engineer",
                    "summary": "Builds useful systems.", "visibility": "published"},
        "experience": [{"id": "exp-1", "employer": "Example Co", "title": "Engineer",
                        "start_date": "2020-01", "end_date": None, "summary": "Built systems.",
                        "order": 1, "visibility": "published"}],
        "education": [], "skills": [], "certifications": [], "contact_links": [],
    }))

    source = load_resume_source(path)

    assert source.profile.id == "profile"
    assert source.experience[0].end_date is None


def test_loader_rejects_unknown_visibility(tmp_path):
    path = tmp_path / "resume.json"
    path.write_text(json.dumps({"profile": {"visibility": "public"}}))

    with pytest.raises(ValidationError):
        load_resume_source(path)
```

- [ ] **Step 2: Run the focused tests and verify they fail**

Run: `pytest tests/content/test_loader.py -q`

Expected: FAIL because the schemas and loader are not defined.

- [ ] **Step 3: Implement the source schemas and loader**

Model the profile, experience, education, skills, certifications, and contact links with stable string IDs, explicit integer ordering where applicable, optional/incomplete dates, safe URL fields, and the three visibility values. Reject duplicate IDs within a section, missing required profile fields, invalid date ordering, and invalid links. Keep source content structured; do not store rendered HTML as the primary field.

- [ ] **Step 4: Add a representative JSON source file and validation CLI**

Seed `content/resume.json` with clearly marked example content, including at least one private or draft record so the privacy path is exercised without making it public. The CLI must print actionable validation errors and exit nonzero on invalid JSON.

- [ ] **Step 5: Run the focused tests and validation command**

Run: `pytest tests/content/test_loader.py -q && python scripts/validate_content.py content/resume.json`

Expected: PASS and a successful validation message.

- [ ] **Step 6: Commit**

```bash
git add app/schemas.py app/content/loader.py content/resume.json scripts/validate_content.py tests/content/test_loader.py
git commit -m "feat: define validated JSON resume content"
```

**Done looks like:** Resume source data has one typed contract, rejects invalid visibility/date/link/identifier data, and can be validated independently of the web app.

**How to check:** Run `python scripts/validate_content.py content/resume.json`; temporarily change a visibility value to `public`, rerun, and confirm a nonzero exit with a field-specific error.

### Task 3: Add SQLite/PostgreSQL persistence and migrations

**Files:**
- Create: `app/db.py`
- Create: `app/models.py`
- Create: `alembic.ini`
- Create: `alembic/env.py`
- Create: `alembic/versions/0001_initial_resume_schema.py`
- Create: `tests/db/test_schema.py`

**Interfaces:**
- Produces `get_session() -> Iterator[Session]`.
- Produces SQLAlchemy models for `Profile`, `Experience`, `Education`, `Skill`, `Certification`, and `ContactLink`.
- Produces `visibility`, `stable_id`, `display_order`, and ownership/profile boundary fields on content records.
- Supports `DATABASE_URL=sqlite:///./data/app.db` locally and a PostgreSQL URL without domain-model changes.

- [ ] **Step 1: Write failing schema tests**

```python
from sqlalchemy import create_engine, inspect

from app.models import Base


def test_initial_schema_contains_resume_sections():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    tables = set(inspect(engine).get_table_names())

    assert {"profiles", "experiences", "educations", "skills",
            "certifications", "contact_links"} <= tables
```

- [ ] **Step 2: Run the focused test and verify it fails**

Run: `pytest tests/db/test_schema.py -q`

Expected: FAIL because the database module and models do not exist.

- [ ] **Step 3: Implement models and session configuration**

Use SQLAlchemy 2 typed mappings. Keep the model portable between SQLite and PostgreSQL, use UTC-aware timestamps where supported, define deterministic ordering indexes, and enforce stable IDs/visibility at the persistence boundary. Make the owner/profile relation explicit even though the first deployment seeds one profile.

- [ ] **Step 4: Create and run the initial Alembic migration**

Generate a reviewed migration matching the models. Configure Alembic to read the same `DATABASE_URL` as the application and fail clearly when it is missing or invalid.

- [ ] **Step 5: Run schema and migration checks**

Run: `pytest tests/db/test_schema.py -q && alembic upgrade head`

Expected: PASS and a local SQLite database with the migrated tables.

- [ ] **Step 6: Commit**

```bash
git add app/db.py app/models.py alembic.ini alembic/env.py alembic/versions tests/db/test_schema.py
git commit -m "feat: add portable resume persistence schema"
```

**Done looks like:** The same domain model can be created through SQLite locally and migrated through Alembic, with explicit ownership, visibility, stable IDs, and ordering.

**How to check:** Set `DATABASE_URL=sqlite:///./data/check.db`, run `alembic upgrade head`, and inspect the tables; run the schema test against an in-memory SQLite engine.

### Task 4: Implement idempotent ingestion and centralized public reads

**Files:**
- Create: `app/content/ingest.py`
- Create: `app/repositories/resume.py`
- Create: `tests/content/test_ingest.py`
- Create: `tests/repositories/test_public_reads.py`
- Create: `scripts/ingest_content.py`

**Interfaces:**
- Produces `ingest_resume(session: Session, source: ResumeSource) -> None`.
- Produces `get_public_resume(session: Session) -> PublicResume`.
- Produces `get_owner_resume(session: Session) -> ResumeSource`.
- Produces an idempotent `scripts/ingest_content.py` command.

- [ ] **Step 1: Write failing ingestion and privacy tests**

```python
def test_ingestion_is_repeatable(session, source):
    ingest_resume(session, source)
    ingest_resume(session, source)

    assert count_rows(session, "experiences") == len(source.experience)


def test_public_read_excludes_drafts_and_private_records(session, source):
    ingest_resume(session, source)

    public = get_public_resume(session)

    assert all(item.visibility == "published" for item in public.all_items())
```

- [ ] **Step 2: Run focused tests and verify they fail**

Run: `pytest tests/content/test_ingest.py tests/repositories/test_public_reads.py -q`

Expected: FAIL because ingestion and repository functions do not exist.

- [ ] **Step 3: Implement transactional, idempotent ingestion**

Upsert by profile and stable section ID, update changed fields, remove or mark obsolete source-owned records deterministically, and commit as one transaction. Abort on validation or database errors; never partially publish a source file.

- [ ] **Step 4: Implement centralized public and owner reads**

Make `get_public_resume` apply the published visibility predicate, profile ownership, and explicit ordering in one repository boundary. Keep owner reads available for fallback generation but do not expose them through public routes.

- [ ] **Step 5: Run tests and the ingestion command**

Run: `pytest tests/content/test_ingest.py tests/repositories/test_public_reads.py -q && python scripts/ingest_content.py content/resume.json`

Expected: PASS; a second command run produces no duplicate records.

- [ ] **Step 6: Commit**

```bash
git add app/content/ingest.py app/repositories/resume.py scripts/ingest_content.py tests/content/test_ingest.py tests/repositories/test_public_reads.py
git commit -m "feat: ingest resume content with public read isolation"
```

**Done looks like:** Re-running ingestion is safe, and every public read path centrally excludes drafts and private records while preserving order.

**How to check:** Ingest twice, query counts, and inspect the public read result; include a private note in source JSON and confirm it is absent from the public object.

### Task 5: Generate and consume the database-independent fallback

**Files:**
- Create: `app/content/fallback.py`
- Create: `app/services/resume.py`
- Create: `tests/content/test_fallback.py`
- Create: `tests/services/test_resume_service.py`
- Modify: `scripts/ingest_content.py`

**Interfaces:**
- Produces `write_public_fallback(resume: PublicResume, path: Path) -> None`.
- Produces `load_public_fallback(path: Path) -> PublicResume`.
- Produces `load_resume_with_fallback(session_factory, fallback_path) -> tuple[PublicResume, Literal["database", "fallback"]]`.

- [ ] **Step 1: Write failing fallback tests**

```python
def test_fallback_contains_only_published_public_content(tmp_path, source, session):
    ingest_resume(session, source)
    path = tmp_path / "fallback.json"

    write_public_fallback(get_public_resume(session), path)
    fallback = load_public_fallback(path)

    assert all(item.visibility == "published" for item in fallback.all_items())


def test_service_uses_fallback_when_database_is_unavailable(tmp_path, public_resume):
    path = tmp_path / "fallback.json"
    write_public_fallback(public_resume, path)

    result, source = load_resume_with_fallback(lambda: raise_database_error(), path)

    assert source == "fallback"
    assert result.profile.id == public_resume.profile.id
```

- [ ] **Step 2: Run focused tests and verify they fail**

Run: `pytest tests/content/test_fallback.py tests/services/test_resume_service.py -q`

Expected: FAIL because fallback generation and service selection are not implemented.

- [ ] **Step 3: Implement public-only fallback serialization**

Serialize only the `PublicResume` view model, include a schema version and generation timestamp, write atomically, and reject an empty/invalid public profile when an existing valid fallback is present. Never serialize owner/private models.

- [ ] **Step 4: Implement database-first service selection**

Attempt the database read, log the failure distinctly, and load the validated fallback only for database availability failures. Do not convert malformed fallback files, validation errors, or missing required files into a successful response.

- [ ] **Step 5: Wire fallback generation into the release command**

Make `scripts/ingest_content.py` validate source content, ingest it, read the public view, and write the fallback as one controlled release operation. A failure must exit nonzero and leave the previous fallback intact.

- [ ] **Step 6: Run tests and simulate an outage**

Run: `pytest tests/content/test_fallback.py tests/services/test_resume_service.py -q`

Expected: PASS, including a simulated database exception.

- [ ] **Step 7: Commit**

```bash
git add app/content/fallback.py app/services/resume.py scripts/ingest_content.py tests/content/test_fallback.py tests/services/test_resume_service.py
git commit -m "feat: serve public resume from validated fallback"
```

**Done looks like:** The latest validated public profile remains readable without a database, while private content cannot enter the fallback.

**How to check:** Generate a fallback, stop or point the app at an unreachable database, request the profile, and confirm the same public content renders with no private record in the response.

### Task 6: Build the public Jinja resume experience

**Files:**
- Create: `app/routes/resume.py`
- Create: `app/templates/base.html`
- Create: `app/templates/resume.html`
- Create: `app/static/styles.css`
- Create: `tests/routes/test_resume.py`

**Interfaces:**
- Produces `GET /` and `GET /resume` HTML routes.
- Routes consume `load_resume_with_fallback` and pass only `PublicResume` to templates.
- Templates expose semantic sections for profile, experience, education, skills, certifications, and contact links.

- [ ] **Step 1: Write failing route tests**

```python
def test_resume_page_contains_core_sections(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "<main" in response.text
    assert "Experience" in response.text
    assert "Education" in response.text
    assert "Skills" in response.text


def test_resume_page_does_not_render_private_content(client):
    response = client.get("/")

    assert "private fixture text" not in response.text
```

- [ ] **Step 2: Run focused tests and verify they fail**

Run: `pytest tests/routes/test_resume.py -q`

Expected: FAIL because route, templates, and static styles do not exist.

- [ ] **Step 3: Implement route and templates**

Use semantic headings, landmarks, lists, accessible link names, deterministic section ordering, document title/description metadata, and a clear contact section. Do not add client-side JavaScript for core content.

- [ ] **Step 4: Add restrained responsive CSS**

Use plain CSS with a readable single-column mobile layout that expands to a comfortable desktop measure, visible focus styles, sufficient contrast, and print-friendly rules. Avoid a visual brand system beyond the content-first baseline.

- [ ] **Step 5: Run route tests and inspect rendered HTML**

Run: `pytest tests/routes/test_resume.py -q`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add app/routes/resume.py app/templates app/static/styles.css tests/routes/test_resume.py
git commit -m "feat: render accessible public resume"
```

**Done looks like:** A visitor can read the complete core resume without JavaScript on mobile or desktop, and the route uses the same database-first/fallback service.

**How to check:** Run the app, open `/` and `/resume`, disable JavaScript (if any is added later), resize to mobile width, and verify all core sections and contact links remain usable.

### Task 7: Add local Codespaces runtime and release workflow

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `.dockerignore`
- Create: `scripts/dev.sh`
- Create: `docs/operations/local-and-azure.md`
- Modify: `.env.example`

**Interfaces:**
- Produces a documented local command sequence: install, migrate, validate, ingest/fallback, run.
- Produces a containerized app that uses SQLite mounted under a local data directory.
- Documents the later Azure VM target without implementing Azure infrastructure in the local task.

- [ ] **Step 1: Write the operational smoke test**

Document and execute:

```bash
cp .env.example .env
alembic upgrade head
python scripts/validate_content.py content/resume.json
python scripts/ingest_content.py content/resume.json
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

- [ ] **Step 2: Run the smoke test before container changes**

Expected: The command sequence identifies any missing dependency, configuration, migration, or release wiring.

- [ ] **Step 3: Add Docker/Codespaces support**

Use a non-root runtime where practical, mount only the local SQLite data directory, pass configuration through environment variables, and do not bake secrets or private content into the image.

- [ ] **Step 4: Document local and Azure assumptions**

Document local SQLite setup and the eventual Azure VM deployment shape: PostgreSQL connection, environment secrets, HTTPS/reverse proxy, firewall boundaries, backups, migration order, and health checks. Mark PostgreSQL as the production persistence target rather than pretending SQLite is an Azure scaling solution.

- [ ] **Step 5: Run the local container smoke test**

Run: `docker compose config && docker compose up --build --abort-on-container-exit`

Expected: Configuration succeeds and the application starts with the seeded fallback and local database.

- [ ] **Step 6: Commit**

```bash
git add Dockerfile docker-compose.yml .dockerignore scripts/dev.sh docs/operations/local-and-azure.md .env.example
git commit -m "feat: add Codespaces local runtime workflow"
```

**Done looks like:** A new Codespaces session can reproduce the app, migrate SQLite, validate and ingest JSON, generate the fallback, and serve the profile without manual database editing.

**How to check:** Follow `docs/operations/local-and-azure.md` from a clean environment and confirm the profile works both with the SQLite database running and with database access disabled.

### Task 8: Add privacy, accessibility, and deployment verification

**Files:**
- Create: `tests/integration/test_public_privacy.py`
- Create: `tests/integration/test_database_outage.py`
- Create: `tests/accessibility/test_resume_accessibility.py`
- Create: `tests/test_release_failure.py`
- Modify: `pyproject.toml`
- Modify: `docs/operations/local-and-azure.md`

**Interfaces:**
- Produces a repeatable `pytest` suite covering the spec acceptance criteria.
- Produces a release check that fails on invalid source, missing database configuration, invalid fallback, or failed migration.
- Produces an accessibility check for semantic landmarks, heading order, links, focus styles, and metadata.

- [ ] **Step 1: Write failing integration and accessibility tests**

```python
def test_private_source_content_is_absent_from_html_and_fallback(app_client):
    html = app_client.get("/").text
    fallback = app_client.get("/resume").text

    assert "private fixture text" not in html
    assert "private fixture text" not in fallback


def test_database_outage_still_returns_profile(outage_client):
    response = outage_client.get("/")

    assert response.status_code == 200
    assert "Ada Example" in response.text
```

- [ ] **Step 2: Run the focused checks and verify they fail**

Run: `pytest tests/integration tests/accessibility tests/test_release_failure.py -q`

Expected: FAIL for any missing privacy, outage, accessibility, or release behavior.

- [ ] **Step 3: Implement test fixtures and explicit failure paths**

Use isolated temporary databases and fallback files. Assert that malformed source and missing production configuration produce nonzero commands and actionable errors, not partial success.

- [ ] **Step 4: Add accessibility and privacy assertions**

Check semantic `main`/heading structure, document metadata, keyboard-visible focus CSS, link destinations, and absence of private content from rendered HTML and serialized public responses.

- [ ] **Step 5: Run the complete available test suite**

Run: `pytest -q`

Expected: PASS with all first-release tests green.

- [ ] **Step 6: Commit**

```bash
git add tests/integration tests/accessibility tests/test_release_failure.py pyproject.toml docs/operations/local-and-azure.md
git commit -m "test: verify privacy availability and release safety"
```

**Done looks like:** The acceptance criteria are executable: privacy is enforced, database outages preserve public availability, accessibility basics are checked, and unsafe releases fail visibly.

**How to check:** Run `pytest -q`; then deliberately provide invalid JSON and an unreachable database and confirm the release command fails while the previous fallback remains available.

## Plan self-review

- **Spec coverage:** Goals and deferred scope are covered by Tasks 1–6; visibility/privacy by Tasks 2, 4, 5, and 8; Git workflow by Tasks 2 and 7; architecture by Tasks 1, 3–6; fallback availability by Tasks 5 and 8; operations by Tasks 3 and 7; accessibility/discoverability by Task 6 and 8; growth-ready ownership and identifiers by Tasks 2–4.
- **Choice resolution:** The plan uses FastAPI/Jinja/plain CSS, JSON, SQLite locally, PostgreSQL on Azure, and a hybrid build/release fallback workflow. The Azure VM target is documented rather than provisioned in the initial local-first implementation.
- **No placeholders:** No task depends on “TBD,” “TODO,” or an unspecified implementation step. Visual design is intentionally constrained to a minimal content-first baseline.
- **Interface consistency:** `ResumeSource`, `PublicResume`, `ingest_resume`, `get_public_resume`, `write_public_fallback`, `load_public_fallback`, and `load_resume_with_fallback` are defined before their consumers.
- **No implementation started:** This document is the only planned artifact; no application code is created by this plan.
