# Same base as API
FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# 1. Copy Monorepo Metadata
COPY pyproject.toml uv.lock /app/

# 2. Copy Source Code
COPY src /app/src

# 3. Install Dependencies
WORKDIR /app/src/edu-worker
ENV UV_PROJECT_ENVIRONMENT=/app/.venv
RUN uv sync --frozen

# 4. Run Worker Script
ENV PATH="/app/.venv/bin:$PATH"
# Assuming you write a script that polls the queue
CMD ["python", "main.py"]
