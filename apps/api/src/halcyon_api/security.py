"""API key check for the endpoints that change data.

Reads are open; anything that writes needs the key. When no key is configured
the dependency lets everything through, which keeps a bare `uvicorn` and the
test suite frictionless - docker-compose sets one, so the containerised stack
is closed by default.
"""

import secrets
from typing import Annotated

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from .config import Settings, get_settings

API_KEY_HEADER = "X-API-Key"

# auto_error=False so a missing header reaches the check below and can be
# reported as 401 with a useful message instead of FastAPI's bare 403.
api_key_scheme = APIKeyHeader(name=API_KEY_HEADER, auto_error=False)

SettingsDep = Annotated[Settings, Depends(get_settings)]


def require_api_key(
    settings: SettingsDep,
    presented: Annotated[str | None, Security(api_key_scheme)] = None,
) -> None:
    if not settings.auth_enabled:
        return

    if presented is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Missing {API_KEY_HEADER} header.",
            headers={"WWW-Authenticate": API_KEY_HEADER},
        )

    # compare_digest, not ==, so a wrong key cannot be discovered one character
    # at a time by timing the response.
    if not secrets.compare_digest(presented, settings.api_key or ""):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key.",
        )


RequireApiKey = Depends(require_api_key)
