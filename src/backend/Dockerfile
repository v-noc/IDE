# Build context must be the repository root so workspace members resolve.
# Example (local): docker build -f src/backend/Dockerfile .

FROM python:3.12-slim AS builder

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

COPY pyproject.toml uv.lock ./

COPY src/backend ./src/backend
COPY src/vn_logger ./src/vn_logger
COPY src/lsp/py ./src/lsp/py

RUN uv sync --project src/backend --frozen --no-dev

FROM python:3.12-slim

WORKDIR /app/src/backend

ENV PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src/backend /app/src/backend
COPY --from=builder /app/src/vn_logger /app/src/vn_logger

# Railway sets PORT; WEB_CONCURRENCY is optional (defaults to 4 workers).
CMD ["sh", "-c", "exec gunicorn app.main:app -w \"${WEB_CONCURRENCY:-4}\" -k uvicorn.workers.UvicornWorker --bind \"0.0.0.0:${PORT:-8000}\""]
