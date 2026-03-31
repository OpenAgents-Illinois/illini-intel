# illini-intel

Agentic basketball intelligence for the Fighting Illini.

The repo is now Python-first:
- `backend/` contains the backend API built with FastAPI
- `frontend/` contains the UI built with vinext
- `docker compose up --build` runs the full local stack

## Local dev

1. Copy envs:
```bash
cp .env.example .env
cp frontend/.env.local.example frontend/.env.local
```

2. Fill `.env` with AWS credentials and Bedrock settings.

3. Start the stack:
```bash
docker compose up --build
```

4. Open:
- `http://localhost:3000`
- `http://localhost:8080/health`

## Backend layout

```text
backend/
  app/
    api/
    clients/
    core/
    models/
    services/
  tests/
```

## Frontend

The frontend consumes SSE events from `/analyze` and renders:
- agent trace
- insight cards
- matchup preview
- prediction

Use vinext for frontend development:
```bash
cd frontend
npm run dev
```

## Status

Rust has been removed from the supported dev path. Python/FastAPI is the source of truth for backend development.
