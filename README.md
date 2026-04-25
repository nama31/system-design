# URL Shortener Service (Production-Ready Homework)

A clean-architecture URL shortener built with **Python + FastAPI + PostgreSQL + Redis**.

## Features

- Base62 encoding from auto-incremented DB IDs.
- `POST /shorten` with URL regex validation.
- `GET /{shortCode}` redirect with selectable `301` or `302`.
- `400` for invalid input, `404` for missing short code.
- Redis read-through cache for hot redirects.
- Dockerized deployment with PostgreSQL and Redis.
- Unit tests with `pytest`.

## Project Structure

```text
src/
  application/      # use cases
  domain/           # entities + base62 + repository contracts
  infrastructure/   # SQLAlchemy + Redis adapters
  presentation/     # DTOs and input validation
  main.py           # FastAPI entrypoint
```

## Run with Docker

```bash
docker compose up --build
```

Service URL: `http://localhost:8000`

## API Examples

### 1) Create short URL

```bash
curl -X POST http://localhost:8000/shorten \
  -H "Content-Type: application/json" \
  -d '{"long_url":"https://example.com/some/very/long/path"}'
```

Example response:

```json
{
  "short_url": "http://localhost:8000/b",
  "short_code": "b"
}
```

### 2) Redirect

```bash
curl -i http://localhost:8000/b
```

Temporary redirect: default `302`.

Permanent redirect:

```bash
curl -i "http://localhost:8000/b?permanent=true"
```

Returns `301`.

## Local Dev (without Docker)

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --app-dir src --reload
```

## Run Tests

```bash
pytest -q
```

## Design Document

Detailed high-level design (schema, scalability, storage estimate, collision prevention):

- `docs/design.md`
