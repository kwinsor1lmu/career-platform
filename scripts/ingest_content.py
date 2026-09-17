from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pydantic import ValidationError

from app.content.ingest import ingest_resume
from app.content.loader import load_resume_source
from app.db import SessionLocal, engine
from app.models import Base


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest a resume content file into the database")
    parser.add_argument("path", type=Path, help="path to the resume JSON file")
    args = parser.parse_args()

    try:
        source = load_resume_source(args.path)
    except FileNotFoundError:
        print(f"Ingestion failed: file not found: {args.path}", file=sys.stderr)
        return 1
    except UnicodeDecodeError as error:
        print(f"Ingestion failed: unable to read {args.path} as UTF-8: {error.reason}", file=sys.stderr)
        return 1
    except OSError as error:
        print(f"Ingestion failed: unable to read {args.path}: {error}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as error:
        print(
            f"Ingestion failed: invalid JSON in {args.path} at line {error.lineno}, "
            f"column {error.colno}: {error.msg}",
            file=sys.stderr,
        )
        return 1
    except ValidationError as error:
        print(f"Ingestion failed for {args.path}:", file=sys.stderr)
        print(error, file=sys.stderr)
        return 1

    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        ingest_resume(session, source)
        session.commit()
    except Exception as exc:  # pragma: no cover - CLI safety net
        session.rollback()
        print(f"Ingestion failed: {exc}", file=sys.stderr)
        return 1
    finally:
        session.close()

    print(
        f"Ingested profile {source.profile.id} from {args.path}: "
        f"{len(source.experience)} experience, {len(source.education)} education, "
        f"{len(source.skills)} skills, {len(source.certifications)} certifications, "
        f"and {len(source.contact_links)} contact links."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
