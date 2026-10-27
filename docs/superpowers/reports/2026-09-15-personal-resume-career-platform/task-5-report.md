# Task 5 report

## Outcome

Implemented database-independent public fallback generation/loading and database-first resume service selection. The fallback contains only the validated `PublicResume` view, carries schema and generation metadata, is written with a temporary file plus `os.replace`, and rejects unpublished content or invalid fallback envelopes. Database fallback is activated only for operational, interface, or disconnection failures; malformed fallback data and application errors remain failures.

The release CLI now validates source JSON, ingests it, commits the database transaction, reads the public view, and atomically publishes the configured fallback. Source validation or fallback publication failures exit nonzero; the atomic replacement preserves the previous fallback.

## Files changed

- `app/content/fallback.py`
- `app/services/__init__.py`
- `app/services/resume.py`
- `scripts/ingest_content.py`
- `tests/conftest.py`
- `tests/content/test_fallback.py`
- `tests/services/__init__.py`
- `tests/services/test_resume_service.py`

## Commands and output

### Focused tests

```bash
pytest tests/content/test_fallback.py tests/services/test_resume_service.py -q
```

```text
....                                                                     [100%]
4 passed in 0.25s
```

### Focused plus regression tests

```bash
pytest tests/content/test_fallback.py tests/services/test_resume_service.py tests/content/test_ingest.py tests/repositories/test_public_reads.py -q
```

```text
........                                                                 [100%]
8 passed in 0.28s
```

### Full test suite

```bash
pytest -q
```

```text
....................                                                     [100%]
20 passed, 1 warning in 1.97s
```

The warning is the existing Starlette/httpx deprecation warning from the health test.

### Release CLI and fallback validation

```bash
tmp=$(mktemp -d) && python scripts/ingest_content.py content/resume.json --fallback "$tmp/fallback.json"
```

```text
Ingested profile profile from content/resume.json and published fallback /tmp/.../fallback.json: 2 experience, 1 education, 2 skills, 1 certifications, and 1 contact links.
fallback=/tmp/.../fallback.json profile=profile items=5
```

The generated fallback reloaded successfully and all five records were published; private/draft source records were absent.

### Outage simulation

A simulated SQLAlchemy `OperationalError` produced:

```text
Database unavailable; loading public resume fallback
outage source=fallback profile=profile
```

The service returned the same public profile from the fallback.

### Failed release preservation

An invalid source file caused a nonzero CLI exit and retained the existing fallback byte-for-byte:

```text
release_failure_preserved_fallback before=d6230963... after=d6230963...
Ingestion failed for .../invalid.json:
4 validation errors for ResumeSource
```

## Self-review

- Serialization uses only public schemas and explicitly rejects a non-published profile or item before creating the replacement file.
- Loading validates the schema version, timestamp, envelope shape, Pydantic content, and published visibility; it does not turn malformed files into successful responses.
- Atomic writes use a same-directory temporary file, flush/fsync, `os.replace`, and directory fsync, so failed serialization or release validation cannot overwrite the prior fallback.
- Service selection is database-first and returns an explicit `("database" | "fallback")` source marker. Only database availability exceptions activate fallback; application errors propagate.
- The release workflow commits ingestion before replacing the fallback, and replacement itself is atomic.
- No owner/private model is serialized or exposed through the fallback path.

## Concerns

- The service currently logs database availability failures with a traceback via `logger.exception`; production logging configuration should route this to the intended operational sink without exposing connection details.
- The fallback path defaults to `data/fallback.json`, which is ignored by git and must be generated as part of deployment/release automation.
- The existing project remains single-owner by design (`owner-1`); multi-tenant fallback selection is out of scope for Task 5.

## Review fix: release transaction ordering

The release path previously committed the database before generating the fallback. It now stages the fallback in the target directory, validates the staged file, and performs ingestion plus fallback generation inside one SQLAlchemy transaction. The database commit occurs only after fallback serialization and validation succeed; the staged file is atomically renamed to the configured fallback path only after the commit. Any fallback failure rolls back the database transaction and removes the staged file, preserving the previous fallback.

### Regression test

```bash
pytest tests/content/test_ingest.py::test_failed_fallback_does_not_publish_database_changes -q
```

```text
.                                                                        [100%]
1 passed in 0.13s
```

The test forces fallback storage failure and verifies that no profile rows remain in the database.

### Covering tests

```bash
pytest tests/content/test_ingest.py tests/content/test_fallback.py tests/services/test_resume_service.py -q
```

```text
........                                                                 [100%]
8 passed in 0.54s
```

### Full suite

```bash
pytest -q
```

```text
.....................                                                    [100%]
21 passed, 1 warning in 2.46s
```

The warning remains the existing Starlette/httpx deprecation warning.

### Self-review

- `ingest_resume(..., commit=False)` allows the release command to own the transaction while preserving the existing committed behavior for all other callers.
- Staging and validation happen before transaction exit, so fallback failures cannot publish database changes.
- The previous fallback is untouched until the database commit succeeds and `os.replace` swaps the validated staged file atomically.
- The remaining filesystem edge case is a failure during the final post-commit rename; this cannot be coordinated atomically with SQLAlchemy, but it cannot expose a partially written fallback and the prior file remains intact if replacement itself fails.
