# CLAUDE.md — illini-intel

## What this is

Agentic Business Intelligence for the Fighting Illini basketball team.
The project now uses a Python/FastAPI backend in `backend/` and a vinext frontend in `frontend/`.

## Backend architecture

- `backend/app/api/routes.py` exposes `/health` and `/analyze`
- `backend/app/services/pipeline.py` runs Scout and Analyst phases
- `backend/app/services/narrator.py` emits frontend-ready BI events
- `backend/app/clients/espn.py` fetches ESPN data
- `backend/app/clients/bedrock.py` calls Bedrock

## Local development

```bash
docker compose up --build
```

Backend-only validation:
```bash
uv run --project backend python -m compileall backend/app backend/tests
```

Frontend validation:
```bash
cd frontend && npm run build
```

Frontend dev:
```bash
cd frontend && npx vinext dev
```

## Event contract

Keep the frontend SSE contract stable. Emit:
- `agent_thought`
- `tool_call`
- `tool_result`
- `insight_card`
- `matchup_preview`
- `prediction`
- `team_header`
- `stat_comparison`
- `report_card`
- `win_probability`
- `done`

Always emit `done` even on failure.
