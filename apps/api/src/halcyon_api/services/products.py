"""Business rules for the product register.

This layer owns the rules and knows nothing about HTTP: it raises the domain
errors below, and main.py is what turns them into status codes. Keeping the
translation in one place is what stops a 404 from being spelled three
different ways across the endpoints.
"""

from sqlalchemy import func
from sqlmodel import Session, select

from ..models import Product, utcnow
from ..schemas import ProductCreate, ProductPatch, ProductUpdate


class ProductError(Exception):
    """Base for everything this module raises."""


class ProductNotFound(ProductError):
    def __init__(self, name: str):
        self.name = name
        super().__init__(f"No product found with the name '{name}'.")


class DuplicateProductName(ProductError):
    def __init__(self, name: str):
        self.name = name
        super().__init__(f"A product named '{name}' already exists.")


class NameMismatch(ProductError):
    def __init__(self, path_name: str, body_name: str):
        self.path_name = path_name
        self.body_name = body_name
        super().__init__(f"Body name '{body_name}' does not match the path name '{path_name}'.")


def find_by_name(session: Session, name: str) -> Product | None:
    return session.exec(select(Product).where(Product.name == name)).first()


def get_by_name(session: Session, name: str) -> Product:
    """The product, or ProductNotFound."""
    if product := find_by_name(session, name):
        return product
    raise ProductNotFound(name)


def reject_duplicate_name(session: Session, name: str, keep_id: int | None = None) -> None:
    """Refuse a name another product already uses.

    keep_id excludes the row being edited, so renaming a product to the name it
    already has is not treated as a clash with itself.
    """
    statement = select(Product).where(Product.name == name)
    if keep_id is not None:
        statement = statement.where(Product.id != keep_id)

    if session.exec(statement).first():
        raise DuplicateProductName(name)


def count(session: Session) -> int:
    return session.exec(select(func.count()).select_from(Product)).one()


def list_page(session: Session, page: int, page_size: int) -> tuple[list[Product], int, int]:
    """One page of products, plus the page actually served and the total count.

    An over-large page is clamped to the last one, so a client walking pages
    always lands somewhere real. Without an explicit order SQLite and Postgres
    may both hand back rows differently per query, which would let a product
    show up on two pages or on none.
    """
    total_items = count(session)
    total_pages = (total_items + page_size - 1) // page_size

    if total_pages > 0:
        page = min(page, total_pages)

    query = select(Product).order_by(Product.id).limit(page_size).offset((page - 1) * page_size)

    return list(session.exec(query).all()), page, total_items


def create(session: Session, path_name: str, data: ProductCreate) -> Product:
    # The path is what addresses the product, so a body that disagrees with it
    # is rejected rather than silently overruled.
    if data.name != path_name:
        raise NameMismatch(path_name, data.name)

    reject_duplicate_name(session, path_name)

    product = Product(**data.model_dump())
    return _save(session, product)


def replace(session: Session, name: str, data: ProductUpdate) -> Product:
    """Full update: every field is overwritten with what was sent."""
    product = get_by_name(session, name)
    reject_duplicate_name(session, data.name, keep_id=product.id)

    for field, value in data.model_dump().items():
        setattr(product, field, value)

    return _save(session, product)


def patch(session: Session, name: str, data: ProductPatch) -> Product:
    """Partial update: only the fields present in the body are touched."""
    product = get_by_name(session, name)
    # exclude_unset keeps an absent field absent; exclude_none stops an
    # explicit null from being written over a real value. 0, False and [] are
    # neither, so they still get through.
    changes = data.model_dump(exclude_unset=True, exclude_none=True)

    # Nothing was sent, so nothing changed: bumping updated_at here would make
    # the column mean "last written to" instead of "last actually modified".
    if not changes:
        return product

    if "name" in changes:
        reject_duplicate_name(session, changes["name"], keep_id=product.id)

    for field, value in changes.items():
        setattr(product, field, value)

    return _save(session, product)


def delete(session: Session, name: str) -> Product:
    """Remove the product and return the row as it was, for the receipt."""
    product = get_by_name(session, name)
    session.delete(product)
    session.commit()
    return product


def _save(session: Session, product: Product) -> Product:
    product.updated_at = utcnow()
    session.add(product)
    session.commit()
    session.refresh(product)
    return product
