"""Pydantic schemas for the product endpoints.

Each verb takes a different shape: POST and PUT require the whole product,
PATCH accepts any subset of its fields, and DELETE answers with a receipt.
"""

from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field
from pydantic import BaseModel
from sqlalchemy import Column, JSON


class ProductBase(SQLModel):
    """The fields every product carries, shared by the table and the schemas."""

    name: str = Field(index=True, unique=True)
    category: str = Field(index=True)
    price: float = Field(index=True)
    stock: int = Field(index=True)
    in_stock: bool = Field(index=True)
    rating: float = Field(index=True)
    tags: list[str] = Field(default_factory=list, sa_column=Column(JSON))


class Product(ProductBase, table=True):
    """The stored row. `id` is the primary key and stays inside the API."""

    id: int | None = Field(default=None, primary_key=True)
    uuid: UUID = Field(default_factory=uuid4, unique=True)


class ProductRead(ProductBase):
    """What every endpoint answers with: the product plus its public uuid."""

    uuid: UUID


class ProductCreate(ProductBase):
    """Body for POST: every field is required, the uuid is server-side."""

    ...


class ProductUpdate(ProductBase):
    """Body for PUT: every field is required, the whole product is replaced."""

    ...


class ProductPatch(ProductBase):
    """Body for PATCH: every field is optional, only what is sent gets changed."""

    name: str | None = None
    category: str | None = None
    price: float | None = None
    stock: int | None = None
    in_stock: bool | None = None
    rating: float | None = None
    tags: list[str] | None = None


class ProductDelete(BaseModel):
    """Confirmation returned after a product is removed."""

    message: str
    uuid: UUID
