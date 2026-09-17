from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable, Literal

from sqlalchemy.exc import DisconnectionError, InterfaceError, OperationalError
from sqlalchemy.orm import Session

from app.content.fallback import load_public_fallback
from app.repositories.resume import PublicResume, get_public_resume

logger = logging.getLogger(__name__)
DatabaseSource = Literal["database", "fallback"]
_DATABASE_AVAILABILITY_ERRORS = (DisconnectionError, InterfaceError, OperationalError)


def load_resume_with_fallback(
    session_factory: Callable[[], Session], fallback_path: Path
) -> tuple[PublicResume, DatabaseSource]:
    session: Session | None = None
    try:
        session = session_factory()
        return get_public_resume(session), "database"
    except _DATABASE_AVAILABILITY_ERRORS:
        logger.exception("Database unavailable; loading public resume fallback")
    except ValueError:
        logger.info("No published resume in database; loading public resume fallback")
    finally:
        if session is not None:
            session.close()
    return load_public_fallback(fallback_path), "fallback"
