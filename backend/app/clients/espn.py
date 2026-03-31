from __future__ import annotations

from typing import Any

import httpx

from app.core.config import ESPN_BASE_URL


def _get_json(path: str, timeout: float = 30.0, params: dict[str, Any] | None = None) -> dict[str, Any]:
    response = httpx.get(f"{ESPN_BASE_URL}{path}", timeout=timeout, params=params)
    response.raise_for_status()
    return response.json()


def fetch_team(team_id: str, timeout: float = 30.0) -> dict[str, Any]:
    return _get_json(f"/teams/{team_id}", timeout=timeout)


def fetch_schedule(team_id: str, timeout: float = 30.0, season: int | None = None) -> dict[str, Any]:
    params = {"season": season} if season is not None else None
    return _get_json(f"/teams/{team_id}/schedule", timeout=timeout, params=params)


def fetch_scoreboard(timeout: float = 30.0) -> dict[str, Any]:
    return _get_json("/scoreboard", timeout=timeout)
