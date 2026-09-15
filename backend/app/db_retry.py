"""
DB retry helper. Wraps SQLAlchemy operations with a single retry
before raising a clean 503 envelope so the process never terminates.
"""
import logging
import time
from typing import TypeVar, Callable, Any

from sqlalchemy.exc import OperationalError
from fastapi import HTTPException

logger = logging.getLogger(__name__)

T = TypeVar("T")


def with_db_retry(fn: Callable[[], T], *, retries: int = 1, delay: float = 0.5) -> T:
    """
    Call ``fn()`` which wraps a DB operation.
    On OperationalError, retry up to ``retries`` times before
    raising an HTTPException(503).
    """
    attempt = 0
    while True:
        try:
            return fn()
        except OperationalError as exc:
            attempt += 1
            if attempt > retries:
                logger.error(f"DB unavailable after {attempt} attempt(s): {exc}")
                raise HTTPException(
                    status_code=503,
                    detail="Database temporarily unavailable. Please retry.",
                )
            logger.warning(f"DB OperationalError (attempt {attempt}/{retries}), retrying in {delay}s…")
            time.sleep(delay)
