"""Storage for the internal product control API.

The records live in a SQLite file next to the project, so they survive an API
restart. The catalogue is data, not source: it is loaded once and then belongs
to the database - see the seeding template at the bottom of this file for how
to add a batch of new items.
"""

from pathlib import Path

from sqlmodel import create_engine, Session, SQLModel

# Anchored to this file, not to the working directory: launching uvicorn from
# somewhere else would otherwise quietly create a second, empty database.
PROJECT_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_DIR / "database.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# SQLite refuses cross-thread use by default, and uvicorn serves requests from
# a thread pool.
CONNECT_ARGS = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=CONNECT_ARGS)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


# ---------------------------------------------------------------------------
# Bulk insert template
#
# The items registered so far are already in database.db - this is kept only
# for the next batch. To load one, uncomment both blocks, fill products_db,
# then call seed_default_products() once from the lifespan in api/main.py:
#
#     from .data import create_db_and_tables, seed_default_products
#     ...
#     create_db_and_tables()
#     seed_default_products()
#
# Comment the call back out afterwards, so a startup does not keep re-reading
# a list the database already holds. `select` has to come back from sqlmodel in
# the import at the top of this file.
#
# products_db = [
#     {
#         "name": "Mechanical Keyboard 60%",
#         "category": "Peripherals",
#         "price": 89.90,
#         "stock": 42,
#         "in_stock": True,
#         "rating": 4.7,
#         "tags": ["gaming", "compact", "hot-swappable"],
#     },
# ]
#
#
# def seed_default_products():
#     """Insert the entries of products_db that are not stored yet.
#
#     The check is by name because names are unique, so running it twice
#     inserts nothing the second time.
#     """
#     from .model import Product
#
#     with Session(engine) as session:
#         existing_names = set(session.exec(select(Product.name)).all())
#
#         for data in products_db:
#             if data["name"] in existing_names:
#                 continue
#             session.add(Product(**data))
#
#         session.commit()
