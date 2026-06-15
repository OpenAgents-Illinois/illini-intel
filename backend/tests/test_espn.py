from __future__ import annotations

from app.clients import espn
from app.core.leagues import get_league


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_fetch_team_builds_league_scoped_url(monkeypatch) -> None:
    seen = {}

    def fake_get(url, timeout=30.0, params=None):
        seen["url"] = url
        return FakeResponse({"team": {"id": "13"}})

    monkeypatch.setattr(espn.httpx, "get", fake_get)
    nba = get_league("nba")

    result = espn.fetch_team(nba, "13")

    assert seen["url"] == (
        "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/13"
    )
    assert result == {"team": {"id": "13"}}


def test_fetch_teams_hits_league_teams_endpoint(monkeypatch) -> None:
    seen = {}

    def fake_get(url, timeout=30.0, params=None):
        seen["url"] = url
        seen["params"] = params
        return FakeResponse({"sports": []})

    monkeypatch.setattr(espn.httpx, "get", fake_get)
    espn.fetch_teams(get_league("nfl"))

    assert seen["url"].endswith("/football/nfl/teams")
    # A high limit is required so ESPN returns the full league, not just the first page.
    assert seen["params"]["limit"] >= 500


def test_fetch_scoreboard_removed() -> None:
    assert not hasattr(espn, "fetch_scoreboard")
