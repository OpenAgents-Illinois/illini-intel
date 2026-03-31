# illini-intel Specification

## Overview

Illini Intel is an agentic basketball intelligence app for Illinois basketball.
The backend gathers team context, reasons over the matchup, and streams a live BI report to the frontend.

The repo now uses a Python backend for local and ongoing development.

## Architecture

```text
Frontend (vinext)
        |
        | EventSource / SSE
        v
Python API (FastAPI)
        |
        +-- ESPN client
        +-- Bedrock client
        +-- pipeline service
        +-- narrator service
```

## Backend responsibilities

### Scout phase
- fetch Illinois team data from ESPN
- fetch opponent data from ESPN
- fetch schedule / scoreboard context
- summarize key context for downstream analysis

### Analyst phase
- reason over scout context
- produce matchup dynamics and risks

### Narrator phase
- emit frontend-ready BI events:
  - `insight_card`
  - `team_header`
  - `win_probability`
  - `stat_comparison`
  - `report_card`
  - `matchup_preview`
  - `prediction`
  - `done`

## Python backend structure

```text
backend/
  app/
    api/
      routes.py
    clients/
      bedrock.py
      espn.py
    core/
      config.py
    models/
      events.py
    services/
      pipeline.py
      narrator.py
  tests/
```

## Local development

Run the stack with:
```bash
docker compose up --build
```

Services:
- frontend: `http://localhost:3000`
- backend: `http://localhost:8080`
- healthcheck: `http://localhost:8080/health`

## Environment

Use `.env.example` as the template for:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_SESSION_TOKEN`
- `AWS_REGION`
- `BEDROCK_MODEL_ID`
- `NEXT_PUBLIC_API_GATEWAY_URL`

## Notes

- The backend uses FastAPI with `uvicorn`
- The backend streams SSE directly from `/analyze`
- Bedrock access must be enabled in AWS for the configured model
