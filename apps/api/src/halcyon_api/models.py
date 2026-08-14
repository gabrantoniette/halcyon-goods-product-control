"""The stored table.

`ProductBase` carries the fields a product has; the table adds the identity
columns. The request and response shapes are built from the same base in
schemas.py, so a field is declared once.
"""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, Column, DateTime
from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    """Timezone-aware now, so timestamps are unambiguous across deployments."""
    return datetime.now(UTC)


class ProductBase(SQLModel):
    """The fields every product carries, shared by the table and the schemas."""

    name: str = Field(index=True, unique=True)
    category: str = Field(index=True)
    price: float = Field(index=True, ge=0)
    stock: int = Field(index=True, ge=0)
    in_stock: bool = Field(index=True)
    rating: float = Field(index=True, ge=0, le=5)
    # NOT NULL with a server default: the Python side always sends a list, and
    # a NULL read back would fail validation against `list[str]`.
    tags: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSON, nullable=False, server_default="[]"),
    )


class Product(ProductBase, table=True):
    """The stored row. `id` is the primary key and never leaves the API."""

    __tablename__ = "product"

    id: int | None = Field(default=None, primary_key=True)
    uuid: UUID = Field(default_factory=uuid4, unique=True, index=True)

    # timezone=True matters on Postgres: a naive column would silently drop the
    # offset that utcnow() attaches, and the timestamps would stop being
    # comparable across deployments.
    created_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
