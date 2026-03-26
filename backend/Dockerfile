FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_LINK_MODE=copy

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml /app/pyproject.toml
COPY backend/pyproject.toml /app/backend/pyproject.toml
COPY frontend/pyproject.toml /app/frontend/pyproject.toml
COPY backend /app/backend
COPY .env /app/.env

RUN uv sync --package backend --no-dev

WORKDIR /app/backend

EXPOSE 8000

CMD ["uv", "run", "--package", "backend", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
