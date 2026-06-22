from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.core.leagues import League


@dataclass
class TeamRef:
    id: str
    name: str
    mascot: str
    color: str | None = None
    rank: int | None = None


@dataclass
class MatchupRequest:
    league_key: str
    team_a_id: str
    team_b_id: str


@dataclass
class MatchupContext:
    league: League
    team_a: TeamRef
    team_b: TeamRef
    head_to_head_event: dict[str, Any] | None
    game_context: str
    stat_table: list[dict[str, Any]] = field(default_factory=list)
    team_a_form: list[str] = field(default_factory=list)
    team_b_form: list[str] = field(default_factory=list)
