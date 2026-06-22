from __future__ import annotations

from app.core.leagues import get_league
from app.models.matchup import MatchupContext, MatchupRequest, TeamRef


def test_matchup_request_holds_raw_selection() -> None:
    req = MatchupRequest(league_key="nba", team_a_id="13", team_b_id="2")
    assert (req.league_key, req.team_a_id, req.team_b_id) == ("nba", "13", "2")


def test_matchup_context_is_symmetric() -> None:
    team_a = TeamRef(id="356", name="Illinois", mascot="Fighting Illini", color="ff5f05", rank=3)
    team_b = TeamRef(id="41", name="UConn", mascot="Huskies", color="0c2340", rank=2)
    ctx = MatchupContext(
        league=get_league("mens-college-basketball"),
        team_a=team_a,
        team_b=team_b,
        head_to_head_event=None,
        game_context="NCAA Men's Basketball Matchup",
        stat_table=[{"stat": "PPG", "team_a": "80.0", "team_b": "78.0"}],
        team_a_form=["W", "W"],
        team_b_form=["L"],
    )
    assert ctx.team_a.name == "Illinois"
    assert ctx.team_b.name == "UConn"
    assert ctx.head_to_head_event is None
    assert ctx.stat_table[0]["team_a"] == "80.0"
