# Task 8 report

## Commands

1. `cd /workspaces/career-platform/.worktrees/personal-resume-platform && pytest tests/integration tests/accessibility tests/test_release_failure.py -q`

Output:

```text
.......                                                                  [100%]
=============================== warnings summary ===============================
../../../../usr/local/python/3.14.2/lib/python3.14/site-packages/fastapi/testclient.py:1
  /usr/local/python/3.14.2/lib/python3.14/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
7 passed, 1 warning in 2.85s
```

2. `cd /workspaces/career-platform/.worktrees/personal-resume-platform && pytest -q`

Output:

```text
..............................                                           [100%]
=============================== warnings summary ===============================
../../../../usr/local/python/3.14.2/lib/python3.14/site-packages/fastapi/testclient.py:1
  /usr/local/python/3.14.2/lib/python3.14/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
30 passed, 1 warning in 3.85s
```

## Self-review

- Privacy coverage is enforced at the public fallback and page-render layer: private fixture text is excluded from HTML, fallback JSON, and public resume data.
- Outage behavior is exercised through a database failure path that still serves the last published profile via the fallback.
- Accessibility checks cover semantic landmarks, heading structure, document metadata, keyboard-focus CSS, and link destinations.
- Release safety checks cover malformed source input, invalid production config, invalid fallback JSON, and migration/release failures failing with clear nonzero exits.
- The repo-level configuration and local/Azure ops docs align with the release guardrail expectations.

## Concerns

- FastAPI TestClient still emits a Starlette deprecation warning when using the httpx-based stack; it does not affect runtime correctness, but the dependency can be upgraded in a future cleanup.
- The project still depends on explicit runtime validation and controlled fallback content for public release safety; any future changes should maintain the same non-silent failure behavior.

## Follow-up fix report

- Tightened the actual `python scripts/ingest_content.py ...` release path to validate `Settings()` before ingesting, reject invalid fallback JSON before touching the fallback, and print actionable `stderr` without a traceback for configuration and release errors.
- Expanded `tests/test_release_failure.py` to exercise the CLI subprocess for malformed source, missing production config, invalid fallback, and database-connection failure, while asserting the last good fallback remains byte-for-byte unchanged.
- Re-ran the focused and full suites; both pass with the stricter release safety checks in place.

## Fix round 2 report

- Added the missing CLI-level release-step failure test for an unreachable PostgreSQL target during the real `python scripts/ingest_content.py` path, asserting a nonzero exit code, actionable stderr text, and no traceback.
- Corrected the invalid-fallback subprocess case to create a valid fallback at the exact target path, then deliberately replace it with invalid JSON before invoking the CLI and assert that the target file bytes remain exactly as corrupted (the script must not rewrite it).
- Re-ran the focused and full suite; both remain green with the final release guardrail checks in place.
