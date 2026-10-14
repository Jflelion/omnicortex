FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

RUN useradd --create-home --uid 1000 appuser \
    && mkdir -p uploads \
    && chown appuser:appuser uploads

USER appuser

EXPOSE 8000

# Apply migrations and seed default roles (both idempotent), then start the API.
CMD ["sh", "-c", "alembic upgrade head && python -m app.database.seed && exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
