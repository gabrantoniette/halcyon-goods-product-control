"""Request and response shapes for the product endpoints.

Each verb takes a different shape: POST and PUT require the whole product,
PATCH accepts any subset of its fields, and DELETE answers with a receipt.
"""

from datetime import UTC, datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from .models import ProductBase


class ProductRead(ProductBase):
    """What every endpoint answers with: the product plus its public identity."""

    uuid: UUID
    created_at: datetime
    updated_at: datetime

    @field_validator("created_at", "updated_at", mode="after")
    @classmethod
    def assume_utc(cls, value: datetime) -> datetime:
        """Label a naive timestamp as UTC.

        Postgres gives these back timezone-aware, SQLite cannot and returns
        them naive. Everything is written as UTC, so labelling it here is what
        keeps the serialised contract identical on both backends.
        """
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value


class ProductCreate(ProductBase):
    """Body for POST: every field is required, the uuid is server-side."""


class ProductUpdate(ProductBase):
    """Body for PUT: every field is required, the whole product is replaced."""


class ProductPatch(BaseModel):
    """Body for PATCH: every field is optional, only what is sent gets changed."""

    name: str | None = None
    category: str | None = None
    price: float | None = Field(default=None, ge=0)
    stock: int | None = Field(default=None, ge=0)
    in_stock: bool | None = None
    rating: float | None = Field(default=None, ge=0, le=5)
    tags: list[str] | None = None


class ProductDelete(BaseModel):
    """Confirmation returned after a product is removed."""

    message: str
    uuid: UUID


class HealthRead(BaseModel):
    status: str
    environment: str
    database: str
    auth_required: bool
