# AGENTS.md — illini-intel

## What this is

Agentic Business Intelligence for the Fighting Illini basketball team.
The backend is now Python/FastAPI based and streams SSE events to the frontend.

Frontend is vinext.
Backend lives in `backend/`.

Read `docs/SPEC.md` and `docs/BUILD.md` before changing architecture.

## Backend stack

- FastAPI
- uvicorn
- boto3
- httpx
- Docker Compose for local orchestration

## Event stream

The frontend expects SSE events shaped like:
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

Always emit `done` at the end or on error.

## Local dev

```bash
docker compose up --build
```

Useful checks:
```bash
uv run --project backend python -m compileall backend/app backend/tests
cd frontend && npm run build
```

## Environment

Copy `.env.example` to `.env` and fill in AWS credentials and Bedrock model settings.
Never commit `.env`.

## ESPN API

Base:
`https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball`

Illinois team ID: `356`
UConn team ID: `41`

## Frontend

`frontend/` connects to `NEXT_PUBLIC_API_GATEWAY_URL + '/analyze'` using `EventSource`.
Use `npx vinext dev` or `npm run dev` for local frontend work.
