"""Settings for the records API.

Everything the API needs to run comes from the environment, so the same image
runs locally against SQLite and in a container against Postgres without a code
change. Values are read once and cached.
"""

import json
from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

# Kept as the default so a clone still runs with no configuration at all.
DEFAULT_DATABASE_URL = "sqlite:///./database.db"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="HALCYON_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = DEFAULT_DATABASE_URL

    # Writes require this key in the X-API-Key header. Left unset the API is
    # open, which is what keeps `pytest` and a bare `uvicorn` frictionless;
    # docker-compose sets it, so the containerised stack is closed by default.
    api_key: str | None = None

    # The web client calls the API from its own server, so this only matters
    # for a browser talking to the API directly.
    #
    # NoDecode turns off the JSON parsing pydantic-settings applies to complex
    # types at the source level. Without it a plain "a,b" from the environment
    # raises before the validator below ever sees it.
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:3000"]
    )

    # Echoed by /health so a deployed instance can be identified.
    environment: str = "development"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_origins(cls, value):
        """Accept `a,b` from the environment as well as a JSON list.

        NoDecode means nothing decodes the JSON form for us any more, so both
        shapes are handled here.
        """
        if not isinstance(value, str):
            return value

        text = value.strip()
        if text.startswith("["):
            return json.loads(text)

        return [origin.strip() for origin in text.split(",") if origin.strip()]

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    @property
    def auth_enabled(self) -> bool:
        return bool(self.api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
