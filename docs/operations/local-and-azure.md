# Local and Azure operations

This document describes the reproducible local/Codespaces workflow for the personal resume platform and the intended later Azure VM release shape. The local runtime uses SQLite for a single instance. Production persistence is PostgreSQL; SQLite is not an Azure scaling solution.

## Local install and release sequence

From the repository root:

```bash
cp .env.example .env
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'

set -a
. ./.env
set +a
alembic upgrade head
python scripts/validate_content.py content/resume.json
python scripts/ingest_content.py content/resume.json
python -m pytest -q
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open `http://127.0.0.1:8000/` and check `http://127.0.0.1:8000/health`. The `data/` directory contains the local SQLite database and generated public fallback. It is ignored by Git. If the database is unavailable after a successful ingest, the public routes use the validated `FALLBACK_PATH` JSON; `/health` remains a process health check and does not claim database readiness.

The one-command local runtime performs the same migration, validation, ingest/fallback, and serve sequence:

```bash
cp .env.example .env
./scripts/dev.sh
```

Docker Compose uses the same script. It passes configuration through `.env`, runs as a non-root user aligned to `HOST_UID`/`HOST_GID` (default `1000:1000`), and persists only the host `./data` directory. Set those two values to the numeric owner of the host checkout before building if your environment uses different IDs; this prevents a host-created `data/app.db` with mode `644` from becoming unwritable in the container:

```bash
cp .env.example .env
docker compose config
docker compose up --build
```

In another terminal, verify the running container:

```bash
curl --fail http://127.0.0.1:8000/health
curl --fail http://127.0.0.1:8000/
```

Stop it with `Ctrl-C`. Do not put credentials in the Dockerfile, Compose file, or image. `.env` is ignored by Git and is supplied at runtime. The checked-in `content/resume.json` is the public seed content; do not replace it with private source material in an image build. For private content, provide a controlled runtime source and set `CONTENT_PATH` without committing it.

## Configuration and secrets

`.env.example` is a non-secret template. At minimum, set:

- `ENVIRONMENT=development` locally; production rejects SQLite.
- `DATABASE_URL=sqlite:///./data/app.db` locally.
- `CONTENT_PATH` to the validated JSON source.
- `FALLBACK_PATH` to the generated public fallback.
- `APP_PORT`, `HOST`, and `PORT` only when changing the local bind/port.

Production secrets are environment-only (or injected by an Azure secret store), never committed, logged, or baked into an image. Use a PostgreSQL URL such as `postgresql+psycopg://user:password@host:5432/database` for production.

## Later Azure VM deployment assumptions

This task does not provision Azure resources. The intended deployment is a private Azure VM or equivalent host running the same image behind a reverse proxy/load balancer:

1. Provision PostgreSQL (prefer Azure Database for PostgreSQL Flexible Server) and a restricted application database identity. Store `DATABASE_URL` and any future secrets in Azure Key Vault or managed deployment secret configuration; inject them only at process start.
2. Build and scan the image in CI. The image contains application code and public seed content only; it contains no `.env`, database file, generated fallback from a developer machine, or private resume source.
3. On release, create/update the container with production environment variables, run `alembic upgrade head` against PostgreSQL before serving traffic, then run the validated ingest/release command from a controlled content source. Never run destructive migration commands automatically.
4. Terminate HTTPS at a managed Application Gateway, reverse proxy, or equivalent. Redirect HTTP to HTTPS, keep the VM/database private where possible, and allow inbound firewall/security-group traffic only from the proxy and administration paths. Do not expose PostgreSQL publicly to the internet.
5. Configure liveness checks to `GET /health` and use restart/rollback behavior for failed processes. `/health` is intentionally lightweight; add a separate authenticated/readiness check before treating database connectivity as healthy.
6. Back up PostgreSQL with automated point-in-time retention and test restores. Back up private content at its controlled source. Do not rely on the container filesystem or local SQLite `data/` mount for production durability.
7. Observe application logs, proxy access/error logs, migration output, disk usage, and backup status. Rotate credentials and certificates without committing them.

Before a release, validate the image and database in staging, then follow this order: backup/confirm rollback, apply migrations, publish content/fallback, switch traffic, check `/health` and the public page, and monitor errors. For a database outage, the public page may continue from the last validated fallback, but ingestion and writes must fail visibly rather than silently creating success-shaped data.
