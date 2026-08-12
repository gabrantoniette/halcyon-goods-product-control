# Build and runtime are separate stages so the compiler and the build caches
# never reach the shipped image.
FROM python:3.13-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

# The dependency list alone first: this layer is only rebuilt when the pins
# change, not on every source edit. The stub package exists because the build
# backend needs something to package - `pip install .` would fail on a missing
# src/halcyon_api, and the real source arrives on the next layer.
COPY pyproject.toml ./
RUN mkdir -p src/halcyon_api \
    && touch src/halcyon_api/__init__.py \
    && python -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip \
    && /opt/venv/bin/pip install .

COPY src ./src
RUN /opt/venv/bin/pip install --no-deps --force-reinstall .


FROM python:3.13-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH"

# curl is the healthcheck; nothing else is added to keep the surface small.
RUN apt-get update \
    && apt-get install --no-install-recommends -y curl \
    && rm -rf /var/lib/apt/lists/*

# A non-root user, so a container escape does not start as root.
RUN useradd --create-home --uid 1001 halcyon

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app
COPY alembic.ini ./
COPY migrations ./migrations
COPY src ./src

USER halcyon

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=3s --start-period=20s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8000/health || exit 1

# Migrations run at start rather than being baked in, so a fresh volume and an
# upgraded one both converge before the API accepts a request.
CMD ["sh", "-c", "alembic upgrade head && uvicorn halcyon_api.main:app --host 0.0.0.0 --port 8000"]
