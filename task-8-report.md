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
7 passed, 1 warning in 1.65s
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
30 passed, 1 warning in 2.87s
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
