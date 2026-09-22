#!/usr/bin/env sh
set -eu

cd "$(dirname "$0")/.."

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  . ./.env
  set +a
fi

: "${DATABASE_URL:?DATABASE_URL must be set; copy .env.example to .env first}"

content_path="${CONTENT_PATH:-content/resume.json}"
fallback_path="${FALLBACK_PATH:-data/fallback.json}"

mkdir -p "$(dirname "$fallback_path")"
alembic upgrade head

if [ -f "$content_path" ]; then
  python scripts/validate_content.py "$content_path"
  python scripts/ingest_content.py "$content_path" --fallback "$fallback_path"
elif [ -f "$fallback_path" ]; then
  echo "Content source not found at $content_path; serving existing fallback $fallback_path."
else
  echo "Neither content source $content_path nor fallback $fallback_path exists." >&2
  exit 1
fi

exec uvicorn app.main:app --host "${HOST:-0.0.0.0}" --port "${PORT:-8000}"
