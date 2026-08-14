"""Product endpoints.

The rules live in services.products; these functions only translate HTTP to it
and back. Products are addressed by name, so names are kept unique: a duplicate
would make an update or a delete ambiguous.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from sqlmodel import Session

from ..db import get_session
from ..schemas import ProductCreate, ProductDelete, ProductPatch, ProductRead, ProductUpdate
from ..security import RequireApiKey
from ..services import products as service

DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 200

SessionDep = Annotated[Session, Depends(get_session)]

router = APIRouter(
    prefix="/products",
    tags=["products"],
    responses={404: {"description": "Product not found"}},
)

# Writes carry the key; reads stay open.
writes = APIRouter(dependencies=[RequireApiKey])


@router.get("", response_model=list[ProductRead])
async def list_products(
    session: SessionDep,
    response: Response,
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
) -> list[ProductRead]:
    """One page of products, with the paging counters returned as headers.

    Clients that need the whole set (the dashboard's totals, chart and filters
    all do) walk the pages using X-Total-Pages.
    """
    items, served_page, total_items = service.list_page(session, page, page_size)
    total_pages = (total_items + page_size - 1) // page_size

    response.headers["X-Page"] = str(served_page)
    response.headers["X-Page-Size"] = str(page_size)
    response.headers["X-Total-Pages"] = str(total_pages)
    response.headers["X-Total-Items"] = str(total_items)

    return [ProductRead.model_validate(item.model_dump()) for item in items]


@router.get("/{product_name}", response_model=ProductRead)
async def get_product_by_name(product_name: str, session: SessionDep) -> ProductRead:
    product = service.get_by_name(session, product_name)
    return ProductRead.model_validate(product.model_dump())


@writes.post("/{product_name}", response_model=ProductRead, status_code=201)
async def create_product(product_name: str, product: ProductCreate, session: SessionDep) -> ProductRead:
    created = service.create(session, product_name, product)
    return ProductRead.model_validate(created.model_dump())


@writes.put("/{product_name}", response_model=ProductRead)
async def replace_product(product_name: str, product: ProductUpdate, session: SessionDep) -> ProductRead:
    updated = service.replace(session, product_name, product)
    return ProductRead.model_validate(updated.model_dump())


@writes.patch("/{product_name}", response_model=ProductRead)
async def update_product_fields(product_name: str, product: ProductPatch, session: SessionDep) -> ProductRead:
    updated = service.patch(session, product_name, product)
    return ProductRead.model_validate(updated.model_dump())


@writes.delete("/{product_name}", response_model=ProductDelete)
async def delete_product(product_name: str, session: SessionDep) -> ProductDelete:
    removed = service.delete(session, product_name)
    return ProductDelete(
        message=f"Product '{product_name}' deleted successfully.",
        uuid=removed.uuid,
    )


router.include_router(writes)
