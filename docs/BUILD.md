# Build Guide

Read `docs/SPEC.md`, `AGENTS.md`, and `.env.example` before changing backend behavior.

## Current stack
- Backend: Python FastAPI in `backend/`
- Frontend: vinext in `frontend/`
- Local orchestration: Docker Compose

## Development workflow
1. Implement the change
2. Run backend validation
3. Run frontend validation if UI changed
4. Bring up the stack with `docker compose up --build`
5. Verify `/health` and `/analyze`

## Useful backend checks
```bash
uv run --project backend python -m compileall backend/app backend/tests
uv run --project backend --group dev pytest backend/tests -q
```

## Useful frontend checks
```bash
cd frontend && npm run build
```

## Frontend dev
```bash
cd frontend && npx vinext dev
```
