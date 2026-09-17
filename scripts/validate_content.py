from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pydantic import ValidationError

from app.content.loader import load_resume_source


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a resume JSON source file")
    parser.add_argument("path", type=Path, help="path to the resume JSON file")
    args = parser.parse_args()

    try:
        source = load_resume_source(args.path)
    except FileNotFoundError:
        print(f"Validation failed: file not found: {args.path}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as error:
        print(
            f"Validation failed: invalid JSON at line {error.lineno}, column {error.colno}: {error.msg}",
            file=sys.stderr,
        )
        return 1
    except ValidationError as error:
        print(f"Validation failed for {args.path}:", file=sys.stderr)
        print(error, file=sys.stderr)
        return 1

    print(
        f"Validated {args.path}: profile and {len(source.experience)} experience, "
        f"{len(source.education)} education, {len(source.skills)} skill, "
        f"{len(source.certifications)} certification, and {len(source.contact_links)} contact link records."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
