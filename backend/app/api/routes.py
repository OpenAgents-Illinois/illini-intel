from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse, PlainTextResponse, StreamingResponse

from app.clients.espn import fetch_teams
from app.core.config import DEFAULT_LEAGUE, DEFAULT_TEAM_A, DEFAULT_TEAM_B
from app.core.leagues import LEAGUES, get_league
from app.models import events
from app.models.matchup import MatchupRequest
from app.services.pipeline import run as run_pipeline

router = APIRouter()
logger = logging.getLogger("illini_intel")


@router.get("/health", response_class=PlainTextResponse)
async def health() -> str:
    return "ok"


@router.get("/leagues")
async def leagues() -> JSONResponse:
    return JSONResponse([{"key": l.key, "label": l.label, "sport": l.sport} for l in LEAGUES.values()])


def _extract_team_options(payload: dict[str, Any]) -> list[dict[str, str]]:
    try:
        raw = payload["sports"][0]["leagues"][0]["teams"]
    except (KeyError, IndexError, TypeError):
        return []
    out = []
    for entry in raw:
        team = entry.get("team", {})
        if team.get("id") and team.get("displayName"):
            out.append({"id": str(team["id"]), "name": team["displayName"]})
    return out


@router.get("/teams")
async def teams(league: str = Query(...)) -> JSONResponse:
    resolved = get_league(league)
    if resolved is None:
        return JSONResponse([], status_code=200)
    payload = await asyncio.to_thread(fetch_teams, resolved)
    return JSONResponse(_extract_team_options(payload))


def _error_stream(message: str) -> StreamingResponse:
    async def gen():
        yield f'data: {json.dumps(events.agent_thought("server", message))}\n\n'
        yield f'data: {json.dumps(events.done())}\n\n'

    return StreamingResponse(gen(), media_type="text/event-stream")


@router.get("/analyze")
async def analyze(
    league: str = Query(default=DEFAULT_LEAGUE),
    team_a: str = Query(default=DEFAULT_TEAM_A),
    team_b: str = Query(default=DEFAULT_TEAM_B),
) -> StreamingResponse:
    if get_league(league) is None:
        return _error_stream(f"Unknown league: {league!r}")
    if team_a == team_b:
        return _error_stream("team_a and team_b must be different")

    request = MatchupRequest(league_key=league, team_a_id=team_a, team_b_id=team_b)
    queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()

    def emit(event: dict[str, Any]) -> None:
        queue.put_nowait(event)

    async def runner() -> None:
        try:
            await asyncio.to_thread(run_pipeline, request, emit)
        except Exception as error:
            logger.exception("pipeline failed")
            queue.put_nowait(events.agent_thought("server", f"Server error: {error!r}"))
            queue.put_nowait(events.done())

    asyncio.create_task(runner())

    async def event_stream():
        while True:
            item = await queue.get()
            yield f"data: {json.dumps(item, default=str)}\n\n"
            if item.get("type") == "done":
                break

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )
