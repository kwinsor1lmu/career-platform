# Task 2 Report

## Files

- `app/schemas.py`: Added the typed `ResumeSource` contract, section models, `Visibility`, constrained IDs, partial dates, strict HTTP(S) links, ordering, and section-local duplicate-ID validation.
- `app/content/loader.py`: Added `load_resume_source(path: Path) -> ResumeSource` using UTF-8 JSON loading and `ResumeSource.model_validate_json`.
- `content/resume.json`: Added representative structured example content across every section, including private and draft records.
- `scripts/validate_content.py`: Added a direct validation CLI with actionable JSON, file, and Pydantic validation errors and nonzero failure exits.
- `tests/content/test_loader.py`: Added focused acceptance and rejection coverage for complete content, visibility, duplicate IDs, date ordering, and invalid links.

## Decisions

- Used Pydantic v2 models with `extra="forbid"` so source content cannot silently grow unsupported fields.
- Kept dates as validated partial ISO strings (`YYYY`, `YYYY-MM`, or `YYYY-MM-DD`) to preserve incomplete source dates while rejecting impossible calendar values and reversed ranges.
- Used `HttpUrl` for contact links so non-HTTP(S) and malformed URLs are rejected.
- Applied duplicate-ID checks independently to each repeatable section, matching the brief’s section-local uniqueness requirement.
- Kept all content structured as fields; no rendered HTML is stored.
- Added a script-root path adjustment so the required direct command `python scripts/validate_content.py content/resume.json` works from a checkout.

## Exact commands and output

`pytest tests/content/test_loader.py -q`

```text
.....                                                                    [100%]
5 passed in 0.16s
```

`python scripts/validate_content.py content/resume.json`

```text
Validated content/resume.json: profile and 2 experience, 1 education, 2 skill, 1 certification, and 1 contact link records.
```

`pytest -q && python scripts/validate_content.py content/resume.json && python - <<'PY' ... ResumeSource.model_validate_json ... PY`

```text
......                                                                   [100%]
6 passed, 1 warning in 0.86s
Validated content/resume.json: profile and 2 experience, 1 education, 2 skill, 1 certification, and 1 contact link records.
ResumeSource.model_validate_json: PASS
```

The full test run emitted one pre-existing dependency warning from Starlette about its `httpx` TestClient integration; it did not affect test results.

Negative CLI check used a temporary JSON file containing `profile.visibility = "public"`:

```text
Validation failed for /tmp/<temporary-file>.json:
...
profile.visibility
  Input should be 'draft', 'private' or 'published' ...
```

The command exited nonzero as required.

## Self-review

- Confirmed the required public interfaces exist: `Visibility`, `ResumeSource.model_validate_json`, and `load_resume_source`.
- Confirmed all six content sections are represented in both the model and fixture.
- Confirmed the valid fixture includes both private and draft records.
- Confirmed invalid visibility, duplicate IDs, reversed dates, malformed links, missing profile fields, invalid JSON, and missing files surface as validation failures rather than silent defaults.
- Ran `git diff --check`; no whitespace errors were reported.
- No unrelated tracked files were modified.

## Concerns

- The full suite still reports the existing Starlette/httpx deprecation warning. It is unrelated to Task 2 and does not fail tests.

## Review Fix: CLI read-error handling

### Finding addressed

The validation CLI now catches UTF-8 decoding failures and filesystem `OSError` failures from `load_resume_source`, including missing paths and directory/unreadable paths. It emits concise path-specific messages and exits nonzero without a traceback. Pydantic JSON-invalid errors are also rendered as an actionable invalid-JSON path message while ordinary schema validation errors remain detailed.

### Additional files and tests

- Updated `scripts/validate_content.py` with explicit `UnicodeDecodeError` and `OSError` handling plus JSON-invalid classification.
- Added `tests/content/test_validate_content.py` covering malformed JSON, invalid UTF-8, missing paths, and unreadable directory paths through the CLI subprocess boundary.

### Exact commands and output

`pytest tests/content/test_validate_content.py -q` (red before the fix):

```text
3 failed, 1 passed in 1.56s
```

The failures demonstrated traceback output for invalid UTF-8 and directory paths, and non-actionable Pydantic JSON-invalid output for malformed JSON.

`pytest tests/content/test_validate_content.py -q` (after the fix):

```text
....                                                                     [100%]
4 passed in 1.61s
```

`pytest tests/content/test_loader.py tests/content/test_validate_content.py -q && python scripts/validate_content.py content/resume.json && git diff --check`:

```text
.........                                                                [100%]
9 passed in 1.33s
Validated content/resume.json: profile and 2 experience, 1 education, 2 skill, 1 certification, and 1 contact link records.
```

### Self-review and concerns

- Missing paths remain a dedicated `file not found` diagnostic because `FileNotFoundError` is caught before the general `OSError` handler.
- Invalid UTF-8 reports the exact path and UTF-8 reason without exposing a traceback.
- Directory and other filesystem read failures report the exact path and underlying OS error.
- Existing schema validation details remain unchanged for non-JSON-invalid `ValidationError` instances.
- No known concerns beyond the pre-existing Starlette/httpx deprecation warning recorded above.
