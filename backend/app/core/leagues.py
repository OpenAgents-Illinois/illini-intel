from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class League:
    key: str        # registry key, e.g. "nba"
    sport: str      # ESPN sport segment, e.g. "basketball"
    path: str       # full ESPN path segment, e.g. "basketball/nba"
    label: str      # display label, e.g. "NBA"


LEAGUES: dict[str, League] = {
    "mens-college-basketball": League(
        "mens-college-basketball", "basketball",
        "basketball/mens-college-basketball", "NCAA Men's Basketball",
    ),
    "nba": League("nba", "basketball", "basketball/nba", "NBA"),
    "nfl": League("nfl", "football", "football/nfl", "NFL"),
    "mlb": League("mlb", "baseball", "baseball/mlb", "MLB"),
    "nhl": League("nhl", "hockey", "hockey/nhl", "NHL"),
}


def get_league(key: str) -> League | None:
    return LEAGUES.get(key)
