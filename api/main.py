from contextlib import asynccontextmanager
from fastapi import FastAPI
from .router import router as products_router
from .data import create_db_and_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    # To load a batch of new items, see the seeding template in api/data.py.
    yield


app = FastAPI(
    title="Halcyon Goods — Internal Product Control API",
    description="Internal product and stock records, consumed by the company client (web and terminal).",
    version="2.0.0",
    lifespan=lifespan,
)
app.include_router(products_router)
