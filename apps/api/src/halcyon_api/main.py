"""The records API.

Schema changes are Alembic's job, so nothing here creates tables: an app that
silently created what a migration should have made would let production drift
away from the migration history without anyone noticing.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import get_settings
from .routers import health, products
from .services.products import DuplicateProductName, NameMismatch, ProductNotFound


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Halcyon Goods — Internal Product Control API",
        description="Internal product and stock records, consumed by the company clients (web and terminal).",
        version="3.0.0",
    )

    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
            expose_headers=["X-Page", "X-Page-Size", "X-Total-Pages", "X-Total-Items"],
        )

    register_error_handlers(app)

    app.include_router(health.router)
    app.include_router(products.router)

    return app


def register_error_handlers(app: FastAPI) -> None:
    """Map the domain errors onto status codes, once, for every endpoint."""

    def as_json(status_code: int, detail: str) -> JSONResponse:
        # Same envelope FastAPI's own HTTPException produces, so clients only
        # ever have to read `detail`.
        return JSONResponse(status_code=status_code, content={"detail": detail})

    @app.exception_handler(ProductNotFound)
    async def _not_found(request: Request, error: ProductNotFound) -> JSONResponse:
        return as_json(404, str(error))

    @app.exception_handler(DuplicateProductName)
    async def _duplicate(request: Request, error: DuplicateProductName) -> JSONResponse:
        return as_json(409, str(error))

    @app.exception_handler(NameMismatch)
    async def _mismatch(request: Request, error: NameMismatch) -> JSONResponse:
        return as_json(422, str(error))


app = create_app()
