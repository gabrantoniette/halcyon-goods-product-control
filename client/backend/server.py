"""Web server for the internal product control client.

It does two jobs: serve the static front-end, and expose the API to the browser
through `api_client`. Going through this layer keeps the browser on a single
origin (so no CORS setup is needed) and means the HTTP logic and the status
messages are written once and shared with the terminal menu.
"""

from pathlib import Path

from fastapi import Body, FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from . import api_client

FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"

# Used when the API is unreachable, so there is no status code to forward.
SERVICE_UNAVAILABLE = 503

app = FastAPI(
    title="Halcyon Goods — Internal Product Control (web client)",
    description="Serves the browser front-end and relays its requests to the records API.",
    version="2.0.0",
)


def relay(result):
    """Forward an api_client result to the browser, preserving the API's status."""
    status = result["status_code"] or SERVICE_UNAVAILABLE
    return JSONResponse(status_code=status, content=result)


@app.get("/api/health")
async def health():
    return {
        "api_up": api_client.is_api_up(),
        "api_base_url": api_client.API_BASE_URL,
    }


@app.get("/api/products")
async def list_products():
    return relay(api_client.list_products())


@app.get("/api/products/{product_name}")
async def get_products_by_name(product_name: str):
    return relay(api_client.get_products_by_name(product_name))


@app.post("/api/products/{product_name}")
async def create_product(product_name: str, product_data: dict = Body(...)):
    return relay(api_client.create_product(product_name, product_data))


@app.put("/api/products/{product_name}")
async def replace_product(product_name: str, product_data: dict = Body(...)):
    return relay(api_client.replace_product(product_name, product_data))


@app.patch("/api/products/{product_name}")
async def update_product_fields(product_name: str, product_data: dict = Body(...)):
    return relay(api_client.update_product_fields(product_name, product_data))


@app.delete("/api/products/{product_name}")
async def delete_product(product_name: str):
    return relay(api_client.delete_product(product_name))


# Mounted last so the /api routes above are matched first.
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
