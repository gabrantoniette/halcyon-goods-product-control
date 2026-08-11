"""Product endpoints for the Halcyon Goods internal product control API.

Products are addressed by name, so names are kept unique: a duplicate would
make an update or a delete ambiguous.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import func
from sqlmodel import Session, select

from .data import get_session
from .model import Product, ProductCreate, ProductDelete, ProductPatch, ProductRead, ProductUpdate

router = APIRouter(
    prefix="/products",
    tags=["products"],
    responses={404: {"description": "Product not found"}},
)

NOT_FOUND = "Product not found"

DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 200

SessionDep = Annotated[Session, Depends(get_session)]

def reject_duplicate_name(session, product_name, keep_id=None):
    """Raise 409 if another product already uses this name.

    keep_id excludes the row being edited, so renaming a product to the name it
    already has is not treated as a clash.
    """
    statement = select(Product).where(Product.name == product_name)
    if keep_id is not None:
        statement = statement.where(Product.id != keep_id)
    if session.exec(statement).first():
        raise HTTPException(status_code=409, detail="A product with this name already exists.")


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
    total_items = session.exec(select(func.count()).select_from(Product)).one()
    total_pages = (total_items + page_size - 1) // page_size

    if total_pages > 0:
        page = min(page, total_pages)

    # Without an explicit order SQLite may hand back rows in a different order
    # per query, which would let a product show up on two pages or on none.
    query = (
        select(Product)
        .order_by(Product.id)
        .limit(page_size)
        .offset((page - 1) * page_size)
    )

    products = session.exec(query).all()

    response.headers["X-Page"] = str(page)
    response.headers["X-Page-Size"] = str(page_size)
    response.headers["X-Total-Pages"] = str(total_pages)
    response.headers["X-Total-Items"] = str(total_items)

    return [ProductRead.model_validate(product) for product in products]


@router.get("/{product_name}", response_model=ProductRead)
async def get_products_by_name(product_name: str, session: SessionDep) -> ProductRead:

    if products := session.exec(select(Product).where(Product.name == product_name)).first():
        return ProductRead.model_validate(products)

    raise HTTPException(status_code=404, detail="No product found with the given name")


@router.post("/{product_name}", response_model=ProductRead, status_code=201)
async def create_product(product_name: str, product: ProductCreate, session: SessionDep) -> ProductRead:
    # The path is what addresses the product, so a body that disagrees with it
    # is rejected rather than silently overruled.
    if product.name != product_name:
        raise HTTPException(
            status_code=422,
            detail=f"Body name '{product.name}' does not match the path name '{product_name}'.",
        )

    reject_duplicate_name(session, product_name)

    new_product = Product(**product.model_dump())
    session.add(new_product)
    session.commit()
    session.refresh(new_product)
    return ProductRead.model_validate(new_product)


@router.put("/{product_name}", response_model=ProductRead)
async def replace_product(product_name: str, product_update: ProductUpdate, session: SessionDep) -> ProductRead:
    if product := session.exec(select(Product).where(Product.name == product_name)).first():
        reject_duplicate_name(session, product_update.name, keep_id=product.id)

        for key, value in product_update.model_dump().items():
            setattr(product, key, value)

        session.add(product)
        session.commit()
        session.refresh(product)

        return ProductRead.model_validate(product)

    raise HTTPException(status_code=404, detail="Product not found.")


@router.patch("/{product_name}", response_model=ProductRead)
async def update_product_fields(product_name: str, product_update: ProductPatch, session: SessionDep) -> ProductRead:

    updated_product = product_update.model_dump(exclude_unset=True, exclude_none=True)

    if product := session.exec(select(Product).where(Product.name == product_name)).first():
        if "name" in updated_product:
            reject_duplicate_name(session, updated_product["name"], keep_id=product.id)

        for key, value in updated_product.items():
            setattr(product, key, value)

        session.add(product)
        session.commit()
        session.refresh(product)

        return ProductRead.model_validate(product)

    raise HTTPException(status_code=404, detail="Product not found.")


@router.delete("/{product_name}", response_model=ProductDelete)
async def delete_product(product_name: str, session: SessionDep) -> ProductDelete:
    if product := session.exec(select(Product).where(Product.name == product_name)).first():
        session.delete(product)
        session.commit()
        return ProductDelete(
            message=f"Product '{product_name}' deleted successfully.",
            uuid=product.uuid,
        )

    raise HTTPException(status_code=404, detail="Product not found.")
