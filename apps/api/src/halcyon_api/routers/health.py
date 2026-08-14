"""Liveness endpoint.

Kept free of authentication and of any database write so a container
healthcheck can call it on a loop.
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlmodel import Session

from ..config import Settings, get_settings
from ..db import get_session
from ..schemas import HealthRead

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthRead)
async def health(
    session: Annotated[Session, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> HealthRead:
    try:
        session.exec(text("SELECT 1"))
        database = "up"
    except Exception:
        database = "down"

    return HealthRead(
        status="ok" if database == "up" else "degraded",
        environment=settings.environment,
        database=database,
        auth_required=settings.auth_enabled,
    )
