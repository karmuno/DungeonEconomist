# -- Build frontend --
FROM node:20-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# -- Production image --
FROM python:3.11-slim
WORKDIR /app

# Install Python dependencies (no dev/test deps needed)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code and data
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Copy built frontend from first stage
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# Create writable data directory for SQLite
RUN mkdir -p data

# Render sets PORT env var; default to 8000
ENV PORT=8000
EXPOSE ${PORT}

CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
