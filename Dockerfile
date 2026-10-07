# -- Compute version from git --
FROM alpine:3 AS version-info
RUN apk add --no-cache bash git
WORKDIR /repo
COPY .git .git
COPY VERSION VERSION
COPY scripts scripts
RUN bash scripts/get-version.sh > /version.txt

# -- Build frontend --
FROM node:20-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
COPY --from=version-info /version.txt /tmp/version.txt
RUN APP_VERSION=$(cat /tmp/version.txt) npm run build

# -- Production image --
FROM python:3.13-slim
WORKDIR /app

# Static uv binary, pinned to match the version this repo's uv.lock was generated with
COPY --from=ghcr.io/astral-sh/uv:0.9.10 /uv /usr/local/bin/uv

# Install from the lock, production group only (no pytest/httpx)
ENV UV_PYTHON_DOWNLOADS=never
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
ENV PATH="/app/.venv/bin:$PATH"

# Copy backend code and data
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Copy built frontend from first stage
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# Bake the version in: this stage has no .git/, VERSION or scripts/ to compute it
COPY --from=version-info /version.txt ./version.txt

# Render sets PORT env var; default to 8000
ENV PORT=8000
EXPOSE ${PORT}

# Run Alembic migrations then start the server
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
