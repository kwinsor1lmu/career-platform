from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pydantic import ValidationError

from app.content.fallback import load_public_fallback, write_public_fallback
from app.content.ingest import ingest_resume
from app.content.loader import load_resume_source
from app.config import Settings
from app.repositories.resume import get_public_resume


def release_resume(session, source, fallback_path: Path) -> None:
    fallback_path.parent.mkdir(parents=True, exist_ok=True)
    fd, staging_name = tempfile.mkstemp(
        prefix=f".{fallback_path.name}.", suffix=".release", dir=fallback_path.parent
    )
    os.close(fd)
    staging_path = Path(staging_name)
    try:
        with session.begin():
            ingest_resume(session, source, commit=False)
            public_resume = get_public_resume(session)
            write_public_fallback(public_resume, staging_path)
            load_public_fallback(staging_path)
        os.replace(staging_path, fallback_path)
    except BaseException:
        session.rollback()
        raise
    finally:
        try:
            staging_path.unlink()
        except FileNotFoundError:
            pass


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest resume content and publish the public fallback")
    parser.add_argument("path", type=Path, help="path to the resume JSON file")
    parser.add_argument("--fallback", type=Path, default=None, help="path to the public fallback JSON")
    args = parser.parse_args()

    try:
        settings = Settings()
    except ValueError as error:
        print(f"Ingestion failed: invalid configuration: {error}", file=sys.stderr)
        return 1

    fallback_path = args.fallback or settings.fallback_path
    if fallback_path.exists():
        try:
            load_public_fallback(fallback_path)
        except (OSError, TypeError, ValueError, json.JSONDecodeError) as error:
            print(f"Ingestion failed: invalid fallback {fallback_path}: {error}", file=sys.stderr)
            return 1

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
        if any(item.get("type") == "json_invalid" for item in error.errors()):
            print(f"Ingestion failed: invalid JSON in {args.path}", file=sys.stderr)
        else:
            print(f"Ingestion failed for {args.path}:", file=sys.stderr)
            print(error, file=sys.stderr)
        return 1

    from app.db import SessionLocal, engine
    from app.models import Base

    try:
        Base.metadata.create_all(bind=engine)
        session = SessionLocal()
        try:
            release_resume(session, source, fallback_path)
        except Exception as exc:  # pragma: no cover - CLI safety net
            session.rollback()
            print(f"Ingestion failed: {exc}", file=sys.stderr)
            return 1
        finally:
            session.close()
    except Exception as exc:  # pragma: no cover - CLI safety net
        print(f"Ingestion failed: {exc}", file=sys.stderr)
        return 1

    print(
        f"Ingested profile {source.profile.id} from {args.path} and published fallback {fallback_path}: "
        f"{len(source.experience)} experience, {len(source.education)} education, "
        f"{len(source.skills)} skills, {len(source.certifications)} certifications, "
        f"and {len(source.contact_links)} contact links."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
