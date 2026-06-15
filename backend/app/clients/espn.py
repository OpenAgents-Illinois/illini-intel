from __future__ import annotations

from typing import Any

import httpx

from app.core.leagues import League

ESPN_API_ROOT = "https://site.api.espn.com/apis/site/v2/sports"


def _get_json(league: League, path: str, timeout: float = 30.0, params: dict[str, Any] | None = None) -> dict[str, Any]:
    url = f"{ESPN_API_ROOT}/{league.path}{path}"
    response = httpx.get(url, timeout=timeout, params=params)
    response.raise_for_status()
    return response.json()


def fetch_team(league: League, team_id: str, timeout: float = 30.0) -> dict[str, Any]:
    return _get_json(league, f"/teams/{team_id}", timeout=timeout)


def fetch_schedule(league: League, team_id: str, timeout: float = 30.0, season: int | None = None) -> dict[str, Any]:
    params = {"season": season} if season is not None else None
    return _get_json(league, f"/teams/{team_id}/schedule", timeout=timeout, params=params)


def fetch_teams(league: League, timeout: float = 30.0) -> dict[str, Any]:
    # ESPN paginates /teams to ~50 by default; a high limit returns the full league
    # (e.g. ~360 D-I basketball teams) so selectors aren't missing teams.
    return _get_json(league, "/teams", timeout=timeout, params={"limit": 1000})
