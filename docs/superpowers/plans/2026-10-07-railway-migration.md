# Railway Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Serve https://kenwinsor.xyz from the existing Railway web service backed by the existing Railway Postgres, with the same resume content the Azure VM serves today, and keep the VM as a rollback.

**Architecture:** Railway builds the repo's existing `Dockerfile` on every push to `main` (the web service is already connected to `github.com/kwinsor1lmu/career-platform`). The container's existing start script `scripts/dev.sh` runs `alembic upgrade head`, validates and ingests `content/resume.json` into Postgres, writes the database-independent fallback to `data/fallback.json` inside the container, then starts uvicorn on Railway's `$PORT`. Your real resume becomes the committed `content/resume.json`, so every deploy rebuilds the database rows and the fallback from git. Cloudflare DNS for `kenwinsor.xyz` and `www` moves from the VM's IP to Railway at the end.

**Tech Stack:** Python 3.12 (Docker), FastAPI, uvicorn 0.54, SQLAlchemy 2.1, psycopg 3, Alembic, Railway (Dockerfile builder, `railway.toml`), Railway Postgres, Cloudflare DNS.

**Spec:** `docs/superpowers/specs/2026-09-15-personal-resume-career-platform-design.md` (sections 5–7: version-controlled content, ingest on deploy, database-independent fallback, PostgreSQL in production). Migration decisions come from the user in the 2026-10-07 `railway-migration` session.

## What was found (inspected 2026-10-07)

| | |
|---|---|
| Running site | VM `20.88.59.204`, commit `8efff7b`, systemd `career-platform` → uvicorn on `127.0.0.1:8000`, nginx + Let's Encrypt in front |
| Live data | VM `~/career-platform/data/app.db` (SQLite, Alembic `0001`, SHA-256 `b817b95c…eded4`): profile `profile` "Kenneth Winsor", 1 experience, 1 education, 8 skills, 0 certifications, 1 contact link, all `published` |
| Data source file | `C:\Users\kenne\Downloads\kenneth-resume.json`. Ingesting it reproduces the VM's public resume byte-for-byte (line endings aside). Checked 2026-10-07. |
| Repo content | `content/resume.json` is still the **placeholder** ("Ada Example", "Python", plus a private demo item) |
| Railway Postgres | Public proxy URL in the main checkout's `.env` as `RAILWAY_DATABASE_URL` (`postgresql://postgres:…@iriguchi.proxy.rlwy.net:26007/railway`) |
| DNS | Cloudflare (`brit`/`rocco.ns.cloudflare.com`). `kenwinsor.xyz` and `www.kenwinsor.xyz` are both A records to `20.88.59.204` |
| Git | `main` = `origin/main` = `92aa193`. The main checkout has **uncommitted UI work** (resume route/template/CSS, favicon, fonts, `.impeccable/`) that is **not** part of this migration |

Two things in the code would break on Railway:

1. **The site would show the placeholder resume.** `scripts/dev.sh` ingests `content/resume.json` on every start. Fixed in Task 3.
2. **The site would lose its styling.** `base.html` builds the stylesheet link with `url_for(...)`, which gives an absolute URL. uvicorn only trusts `X-Forwarded-Proto` from `127.0.0.1`. Behind Railway's edge proxy it would emit `http://kenwinsor.xyz/static/styles.css` on an `https://` page, and browsers block that as mixed content. On the VM it works because nginx connects from `127.0.0.1`. Fixed in Task 2.

There's also one hardening fix: Railway hands out `postgresql://` URLs. SQLAlchemy 2.1 maps those to psycopg, but `pyproject.toml` allows SQLAlchemy ≥ 2.0.32, which maps them to psycopg2. psycopg2 isn't installed, so the app would crash. Fixed in Task 1.

## Global Constraints

- Work in a git worktree on branch `railway-migration` at `C:\Users\kenne\Desktop\ISBA\career-platform-railway`, created from `main` (`92aa193`). Never commit, stash, or reset the uncommitted work in the main checkout `C:\Users\kenne\Desktop\ISBA\career-platform`.
- Python for tests and scripts: the main checkout's venv, `C:/Users/kenne/Desktop/ISBA/career-platform/.venv/Scripts/python`, run with the worktree as the working directory. pytest's `pythonpath = ["."]` makes the worktree's `app` package win.
- A push to `main` deploys to Railway. Push exactly once, in Task 5, after the user says yes. Don't push earlier commits.
- Don't print or commit `RAILWAY_DATABASE_URL` or its password. Read it from the main checkout's `.env` into an environment variable only.
- Don't change the Azure VM, its NSG, or its files. It stays running as the rollback.
- The user changes Railway variables, Railway domains and Cloudflare DNS in their dashboards. Claude gives exact values and verifies with read-only commands.
- Railway variables on the web service: `DATABASE_URL=${{Postgres.DATABASE_URL}}` (use the Postgres service's name as Railway shows it) and `ENVIRONMENT=production`. Don't set `PORT`, because Railway injects it.
- Check pages with `GET` (`curl -s`), not `HEAD`. FastAPI returns `405` to `HEAD /`.
- Full test suite: `.../python -m pytest -q` (about 2.5 minutes on this laptop). Baseline is green.

## Review Focus

1. **Unstyled site behind the proxy.** If `FORWARDED_ALLOW_IPS` isn't trusted, the stylesheet link becomes `http://` and the page renders as plain HTML. Task 2 pins it with a test, and Task 5 checks the live `<link>` starts with `https://`.
2. **The placeholder, or a merge of placeholder and real content, goes live.** The Railway database may already hold placeholder rows from an earlier auto-deploy. Ingest keys on profile id `profile` (the same in both files) and deletes rows missing from the source, so a real ingest replaces them. Task 4 records the database's state first, then compares the rehearsed public resume with the VM's byte-for-byte.
3. **`DATABASE_URL` is missing or still SQLite on Railway.** `dev.sh` exits with "DATABASE_URL must be set", or `Settings` rejects SQLite in production, and the deploy crash-loops. Task 5 Step 1 checks both variables before the push, and Step 4 reads the deploy log for the ingest line.
4. **Uncommitted UI work gets deployed by accident.** Task 5 Step 2 checks that `origin/main..railway-migration` touches only this plan's files before pushing.
5. **Cloudflare proxy (orange cloud) is left on.** Railway can't issue its certificate, and visitors can hit redirect loops or errors. Task 6 sets both records to "DNS only" and checks that the certificate issuer is Let's Encrypt from Railway, not Cloudflare.

---

### Task 1: Pin the psycopg driver for plain `postgresql://` URLs

**Files:**
- Modify: `app/config.py` (the `validate_database_url` validator)
- Create: `tests/test_config.py`

**Interfaces:**
- Consumes: nothing new.
- Produces: `Settings().database_url` always starts with `sqlite://` or `postgresql+psycopg://`. `app/db.py` and `alembic/env.py` already read it from `Settings`, so both pick this up without changes.

- [ ] **Step 1: Create the worktree**

```bash
cd "C:/Users/kenne/Desktop/ISBA/career-platform"
git worktree add -b railway-migration ../career-platform-railway main
cd ../career-platform-railway
git log -1 --format=%h   # 92aa193
```

- [ ] **Step 2: Write the failing tests** in `tests/test_config.py`

```python
import pytest

from app.config import Settings


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
```

- [ ] **Step 3: Run them to verify the first fails**

Run: `C:/Users/kenne/Desktop/ISBA/career-platform/.venv/Scripts/python -m pytest tests/test_config.py -v`
Expected: `test_plain_postgresql_url_uses_psycopg_driver` and `test_production_accepts_railway_postgres_url` FAIL (the URL comes back unchanged). The other three PASS.

- [ ] **Step 4: Implement.** In `app/config.py`, at the end of `validate_database_url`, replace `return normalized` with:

```python
        if normalized.startswith("postgresql://"):
            # Railway and most hosts hand out postgresql://, which older SQLAlchemy maps to psycopg2.
            normalized = "postgresql+psycopg://" + normalized.removeprefix("postgresql://")
        return normalized
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `C:/Users/kenne/Desktop/ISBA/career-platform/.venv/Scripts/python -m pytest tests/test_config.py -v`
Expected: 5 passed.

- [ ] **Step 6: Commit**

```bash
git add app/config.py tests/test_config.py
git commit -m "fix: use psycopg driver for plain postgresql:// database URLs"
```

---

### Task 2: Railway deploy config and proxy trust

**Files:**
- Create: `railway.toml`
- Modify: `Dockerfile` (the first `ENV` block)
- Create: `tests/test_deploy_config.py`

**Interfaces:**
- Consumes: the Dockerfile's existing `CMD ["./scripts/dev.sh"]` and the app's `/health` route.
- Produces: Railway builds with the Dockerfile, waits for `/health` before switching traffic, and restarts on failure. uvicorn trusts `X-Forwarded-Proto` from Railway's edge, so `url_for` produces `https://` URLs.

- [ ] **Step 1: Write the failing test** in `tests/test_deploy_config.py`

```python
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_railway_builds_dockerfile_and_gates_on_health():
    config = tomllib.loads((ROOT / "railway.toml").read_text(encoding="utf-8"))

    assert config["build"]["builder"] == "DOCKERFILE"
    assert config["deploy"]["healthcheckPath"] == "/health"
    assert "startCommand" not in config["deploy"], "the Dockerfile CMD (scripts/dev.sh) must stay the start command"


def test_container_trusts_proxy_forwarded_headers():
    # Without this, url_for() emits http:// asset URLs behind Railway's HTTPS edge and browsers block the stylesheet.
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert 'FORWARDED_ALLOW_IPS="*"' in dockerfile
```

- [ ] **Step 2: Run it to verify it fails**

Run: `C:/Users/kenne/Desktop/ISBA/career-platform/.venv/Scripts/python -m pytest tests/test_deploy_config.py -v`
Expected: FAIL with `FileNotFoundError` for `railway.toml`, and an assertion error for the Dockerfile.

- [ ] **Step 3: Create `railway.toml`**

```toml
[build]
builder = "DOCKERFILE"
dockerfilePath = "Dockerfile"

[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 300
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10
```

- [ ] **Step 4: Edit the Dockerfile.** Change the first `ENV` block to:

```dockerfile
# FORWARDED_ALLOW_IPS lets uvicorn trust the hosting proxy's X-Forwarded-Proto so url_for() builds https:// URLs.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    FORWARDED_ALLOW_IPS="*"
```

uvicorn reads `$FORWARDED_ALLOW_IPS` natively, so `scripts/dev.sh` doesn't change. Trusting `*` is safe here because only Railway's proxy can reach the container.

- [ ] **Step 5: Run the tests to verify they pass**

Run: `C:/Users/kenne/Desktop/ISBA/career-platform/.venv/Scripts/python -m pytest tests/test_deploy_config.py -v`
Expected: 2 passed.

- [ ] **Step 6: Commit**

```bash
git add railway.toml Dockerfile tests/test_deploy_config.py
git commit -m "build: add Railway config and trust proxy forwarded headers"
```

---

### Task 3: Make the real resume the committed content

**Files:**
- Modify: `content/resume.json` (replaced by `C:\Users\kenne\Downloads\kenneth-resume.json`)

**Interfaces:**
- Consumes: `scripts/validate_content.py`.
- Produces: `content/resume.json` with profile id `profile`, name "Kenneth Winsor", 1/1/8/0/1 records, all `published`. Task 4 and every Railway deploy ingest this file.

- [ ] **Step 1: Confirm the source file hasn't changed since inspection**

```bash
C:/Users/kenne/Desktop/ISBA/career-platform/.venv/Scripts/python scripts/validate_content.py ~/Downloads/kenneth-resume.json
```
Expected: `Validated …: profile and 1 experience, 1 education, 8 skill, 0 certification, and 1 contact link records.` If the counts differ, stop and ask the user which version is current.

- [ ] **Step 2: Replace the placeholder and validate it**

```bash
cp ~/Downloads/kenneth-resume.json content/resume.json
C:/Users/kenne/Desktop/ISBA/career-platform/.venv/Scripts/python scripts/validate_content.py content/resume.json
grep -c "Ada Example\|Unpublished skill\|private-project" content/resume.json   # expect 0
```

- [ ] **Step 3: Run the full suite.** No test reads `content/resume.json`, but this confirms it.

Run: `C:/Users/kenne/Desktop/ISBA/career-platform/.venv/Scripts/python -m pytest -q`
Expected: all pass (the baseline count plus the 7 new tests from Tasks 1–2).

- [ ] **Step 4: Commit**

```bash
git add content/resume.json
git commit -m "content: replace placeholder resume with Kenneth Winsor's published resume"
```

---

### Task 4: Rehearse migrate + ingest against Railway Postgres from the laptop

This runs exactly what the first deploy will run, through Railway's public proxy, so any Postgres problem shows up before the push. It is idempotent, and the deploy repeats it.

**Files:**
- Create (scratchpad only, not committed): `C:/Users/kenne/AppData/Local/Temp/claude/C--Users-kenne-Desktop-ISBA-career-platform/b6403db5-06c9-4b47-b161-63217715c952/scratchpad/dump_public.py`, `C:/Users/kenne/AppData/Local/Temp/claude/C--Users-kenne-Desktop-ISBA-career-platform/b6403db5-06c9-4b47-b161-63217715c952/scratchpad/from_vm.txt`, `C:/Users/kenne/AppData/Local/Temp/claude/C--Users-kenne-Desktop-ISBA-career-platform/b6403db5-06c9-4b47-b161-63217715c952/scratchpad/from_railway.txt`

**Interfaces:**
- Consumes: Task 1's normalized URL, Task 3's `content/resume.json`.
- Produces: Railway Postgres at Alembic `0001`, holding the real resume.

- [ ] **Step 1: Load the URL without printing it, and write the dump helper**

```bash
export DATABASE_URL="$(grep '^RAILWAY_DATABASE_URL=' C:/Users/kenne/Desktop/ISBA/career-platform/.env | cut -d= -f2-)"
export ENVIRONMENT=production
test -n "$DATABASE_URL" && echo "url loaded"
```

`C:/Users/kenne/AppData/Local/Temp/claude/C--Users-kenne-Desktop-ISBA-career-platform/b6403db5-06c9-4b47-b161-63217715c952/scratchpad/dump_public.py`:

```python
import json
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import Settings
from app.content.fallback import _resume_payload
from app.repositories.resume import get_public_resume

url = sys.argv[1] if len(sys.argv) > 1 else Settings().database_url
with sessionmaker(bind=create_engine(url))() as session:
    print(json.dumps(_resume_payload(get_public_resume(session)), sort_keys=True))
```

- [ ] **Step 2: Record what's in the Railway database now**

```bash
PYTHONPATH=. C:/Users/kenne/Desktop/ISBA/career-platform/.venv/Scripts/python -c "
from sqlalchemy import create_engine, inspect, text
from app.config import Settings
e = create_engine(Settings().database_url); tables = inspect(e).get_table_names(); print('tables:', sorted(tables))
if 'profiles' in tables:
    with e.connect() as c: print(c.execute(text('select id, name from profiles')).all(), c.execute(text('select * from alembic_version')).all())
"
```
Expected: either no tables (fresh), or the placeholder `('profile', 'Ada Example')` from an earlier auto-deploy. Both are fine. **Stop and ask** if it holds anything else, because ingest would delete rows that aren't in the file.

- [ ] **Step 3: Migrate and ingest**

```bash
C:/Users/kenne/Desktop/ISBA/career-platform/.venv/Scripts/alembic upgrade head
C:/Users/kenne/Desktop/ISBA/career-platform/.venv/Scripts/python scripts/ingest_content.py content/resume.json --fallback "C:/Users/kenne/AppData/Local/Temp/claude/C--Users-kenne-Desktop-ISBA-career-platform/b6403db5-06c9-4b47-b161-63217715c952/scratchpad/railway-fallback.json"
```
Expected: `Running upgrade  -> 0001` (or nothing, if already at head), then `Ingested profile profile from content/resume.json … 1 experience, 1 education, 8 skills, 0 certifications, and 1 contact links.`

- [ ] **Step 4: Compare with the VM byte-for-byte**

```bash
ssh -i ~/.ssh/isba4775_azure azureuser@20.88.59.204 'cd ~/career-platform && PYTHONPATH=. .venv/bin/python - sqlite:///./data/app.db' < "C:/Users/kenne/AppData/Local/Temp/claude/C--Users-kenne-Desktop-ISBA-career-platform/b6403db5-06c9-4b47-b161-63217715c952/scratchpad/dump_public.py" > "C:/Users/kenne/AppData/Local/Temp/claude/C--Users-kenne-Desktop-ISBA-career-platform/b6403db5-06c9-4b47-b161-63217715c952/scratchpad/from_vm.txt"
PYTHONPATH=. C:/Users/kenne/Desktop/ISBA/career-platform/.venv/Scripts/python "C:/Users/kenne/AppData/Local/Temp/claude/C--Users-kenne-Desktop-ISBA-career-platform/b6403db5-06c9-4b47-b161-63217715c952/scratchpad/dump_public.py" > "C:/Users/kenne/AppData/Local/Temp/claude/C--Users-kenne-Desktop-ISBA-career-platform/b6403db5-06c9-4b47-b161-63217715c952/scratchpad/from_railway.txt"
cmp <(tr -d '\r' < "C:/Users/kenne/AppData/Local/Temp/claude/C--Users-kenne-Desktop-ISBA-career-platform/b6403db5-06c9-4b47-b161-63217715c952/scratchpad/from_vm.txt") <(tr -d '\r' < "C:/Users/kenne/AppData/Local/Temp/claude/C--Users-kenne-Desktop-ISBA-career-platform/b6403db5-06c9-4b47-b161-63217715c952/scratchpad/from_railway.txt") && echo IDENTICAL
```
Expected: `IDENTICAL`. Railway Postgres now serves exactly what the VM serves. Nothing to commit.

---

### Task 5: Deploy to Railway

**Files:** none changed. This is a deploy and verify task.

**Interfaces:**
- Consumes: commits from Tasks 1–3, the database from Task 4.
- Produces: the Railway web service running branch `main` at the new head, on its `*.up.railway.app` domain.

- [ ] **Step 1 (user, Railway dashboard): set the web service's variables.** Open web service → Variables:
  - `DATABASE_URL` = `${{Postgres.DATABASE_URL}}` (the private-network URL; use the reference picker so the service name matches)
  - `ENVIRONMENT` = `production`
  - Delete any `PORT`, `HOST`, `CONTENT_PATH` or `FALLBACK_PATH` overrides, if present. The defaults are correct.
  Note the service's generated domain (Settings → Networking). If there isn't one, click "Generate Domain". Below it's called `$RAILWAY_HOST`.

- [ ] **Step 2: Check exactly what will be deployed**

```bash
git fetch origin
git log --oneline origin/main..railway-migration      # exactly the 3 commits from Tasks 1–3
git diff --stat origin/main..railway-migration        # only: app/config.py, tests/test_config.py, railway.toml, Dockerfile, tests/test_deploy_config.py, content/resume.json
git merge-base --is-ancestor origin/main railway-migration && echo fast-forward-ok
```
If any UI file (`app/templates/*`, `app/static/*`, `app/routes/resume.py`) shows up, stop.

- [ ] **Step 3: Ask the user, then push.** Pushing to `main` publishes the deploy. Ask: "Push `railway-migration` to `main` now? Railway will deploy it." Only after a yes:

```bash
git push origin railway-migration:main
```

- [ ] **Step 4 (user shares, or Claude reads if the Railway CLI is set up): the deploy log** must show, in order: `Running upgrade` (or nothing), `Validated content/resume.json…`, `Ingested profile profile from content/resume.json and published fallback data/fallback.json: 1 experience, 1 education, 8 skills, 0 certifications, and 1 contact links.`, then uvicorn `Uvicorn running on http://0.0.0.0:<PORT>`. The deployment turns Active once `/health` passes.

- [ ] **Step 5: Verify the Railway domain**

```bash
H=https://$RAILWAY_HOST
curl -s $H/health                                                    # {"status":"ok"}
curl -s $H/ | grep -c "Kenneth Winsor"                               # ≥ 1
curl -s $H/ | grep -c "Ada Example"                                  # 0
curl -s $H/ | grep -o '<link rel="stylesheet"[^>]*>'                 # href="https://$RAILWAY_HOST/static/styles.css"
curl -s -o /dev/null -w "%{http_code} %{content_type}\n" $H/static/styles.css   # 200 text/css…
```
If the stylesheet `href` starts with `http://`, the `FORWARDED_ALLOW_IPS` change didn't make it into the image. Check the build log's Dockerfile steps.

**Rollback for this task:** nothing public has moved yet. `kenwinsor.xyz` still points at the VM.

---

### Task 6: Move kenwinsor.xyz to Railway

**Files:** none.

**Interfaces:**
- Consumes: the verified Railway deployment from Task 5.
- Produces: `kenwinsor.xyz` and `www.kenwinsor.xyz` served by Railway over HTTPS.

- [ ] **Step 1 (user, Railway): add the custom domains.** Web service → Settings → Networking → Custom Domain. Add `kenwinsor.xyz`, then `www.kenwinsor.xyz`. Leave the port at the default, because the app listens on Railway's `$PORT`. For each domain, Railway shows a CNAME target and a `_railway-verify…` TXT record. Copy them.

- [ ] **Step 2 (user, Cloudflare → kenwinsor.xyz → DNS):**
  - Write down the current records first. This is the rollback: `A @ 20.88.59.204` and `A www 20.88.59.204`.
  - Delete both A records. Add `CNAME @ → <Railway target for apex>` and `CNAME www → <Railway target for www>`. Set **Proxy status: DNS only (grey cloud)** on both. Cloudflare flattens the apex CNAME automatically.
  - Add each `TXT` verification record exactly as Railway shows it.

- [ ] **Step 3: Wait for DNS and the certificate, then verify**

```bash
nslookup kenwinsor.xyz 1.1.1.1          # must no longer answer 20.88.59.204
nslookup www.kenwinsor.xyz 1.1.1.1
for h in kenwinsor.xyz www.kenwinsor.xyz; do
  curl -s -o /dev/null -w "$h %{http_code}\n" https://$h/
  curl -s https://$h/ | grep -o '<link rel="stylesheet"[^>]*>'
  curl -s -D - -o /dev/null https://$h/ | grep -i '^server:'    # not "nginx/1.24.0 (Ubuntu)"
  echo | openssl s_client -connect $h:443 -servername $h 2>/dev/null | openssl x509 -noout -issuer -enddate
done
```
Expected: `200`, an `https://<that host>/static/styles.css` stylesheet, no nginx `Server` header, and an issuer of Let's Encrypt (R1x/E-series) with a fresh end date. Railway's certificate can take several minutes after the TXT check passes. Re-run until it shows.

**Rollback:** in Cloudflare, delete the two CNAMEs and restore `A @ 20.88.59.204` and `A www 20.88.59.204` (DNS only). The VM never stopped serving.

---

### Task 7: Document how the site runs now

**Files:**
- Create: `docs/operations/railway.md`
- Add: `docs/superpowers/plans/2026-10-07-railway-migration.md` (this plan, copied from the main checkout, where it's untracked)

**Interfaces:**
- Consumes: the values verified in Tasks 5–6.
- Produces: an operations note for future updates.

- [ ] **Step 1: Write `docs/operations/railway.md`**

```markdown
# Running on Railway

The site at https://kenwinsor.xyz runs on Railway. The web service is built from this repo's `Dockerfile` on every push to `main`; Railway Postgres stores the resume.

## Deploys

Each deploy runs `scripts/dev.sh`: `alembic upgrade head`, validate and ingest `content/resume.json` into Postgres, write the database-independent fallback to `data/fallback.json` inside the container, then start uvicorn on Railway's `$PORT`. Railway switches traffic once `/health` answers (`railway.toml`).

## Updating the resume

Edit `content/resume.json`, run `python scripts/validate_content.py content/resume.json`, commit, and push to `main`. Items marked `private` or `draft` are stored but never shown.

## Configuration

Web service variables: `DATABASE_URL=${{Postgres.DATABASE_URL}}` and `ENVIRONMENT=production`. The Dockerfile sets `FORWARDED_ALLOW_IPS="*"` so links and the stylesheet use `https://` behind Railway's proxy.

## DNS and rollback

Cloudflare holds `kenwinsor.xyz` and `www` as DNS-only CNAMEs to Railway, which issues the certificate. The old Azure VM (`20.88.59.204`) still serves the previous version; to roll back, replace both CNAMEs with `A 20.88.59.204` records.
```

- [ ] **Step 2: Commit and push** (docs only, so a redeploy with no code change is harmless. Ask before pushing.)

```bash
cp C:/Users/kenne/Desktop/ISBA/career-platform/docs/superpowers/plans/2026-10-07-railway-migration.md docs/superpowers/plans/
git add docs/operations/railway.md docs/superpowers/plans/2026-10-07-railway-migration.md
git commit -m "docs: explain how the site runs on Railway"
git push origin railway-migration:main
```

- [ ] **Step 3: Hand back.** Tell the user that the main checkout's local `main` is now behind `origin/main`. Their uncommitted UI work touches different files, so `git pull --ff-only` in the main checkout is safe whenever they want it. Remove the worktree with `git worktree remove ../career-platform-railway` once the branch is merged. Shutting down the VM is a separate decision; once DNS has moved, its certbot renewal will fail (harmless; nothing is served from it).
