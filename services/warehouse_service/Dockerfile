FROM python:3.13-alpine

WORKDIR /app

RUN apk add --no-cache gcc musl-dev postgresql-dev

RUN pip install --no-cache-dir poetry

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

COPY src/ ./src/
COPY migrations/ ./migrations/
COPY yoyo.ini ./

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
