FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_LINK_MODE=copy

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml /app/pyproject.toml
COPY frontend/pyproject.toml /app/frontend/pyproject.toml
COPY backend/pyproject.toml /app/backend/pyproject.toml
COPY frontend /app/frontend
COPY .env /app/.env

RUN uv sync --package frontend --no-dev

WORKDIR /app/frontend

EXPOSE 8501

CMD ["uv", "run", "--package", "frontend", "streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]
