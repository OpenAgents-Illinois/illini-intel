from __future__ import annotations

from app.core.leagues import get_league
from app.models.matchup import MatchupRequest
from app.services import pipeline

NCAA = get_league("mens-college-basketball")


class RecordingEmitter:
    def __init__(self) -> None:
        self.events = []

    def __call__(self, event):
        self.events.append(event)


def _illinois_payload():
    return {
        "team": {"id": "356", "shortDisplayName": "Illinois", "name": "Fighting Illini", "color": "ff5f05"},
        "nextEvent": [{"competitions": [{"competitors": [
            {"team": {"id": "356"}, "curatedRank": {"current": 8}},
        ]}]}],
    }


def _uconn_payload():
    return {
        "team": {"id": "41", "shortDisplayName": "UConn", "name": "Huskies", "color": "0c2340"},
        "nextEvent": [{"competitions": [{"competitors": [
            {"team": {"id": "41"}, "curatedRank": {"current": 5}},
        ]}]}],
    }


def _schedule_with_h2h():
    return {"events": [{
        "competitions": [{
            "notes": [{"headline": "Men's Basketball Championship - East Region - Elite 8"}],
            "competitors": [
                {"team": {"id": "356", "shortDisplayName": "Illinois", "name": "Fighting Illini"}, "curatedRank": {"current": 3}},
                {"team": {"id": "41", "shortDisplayName": "UConn", "name": "Huskies"}, "curatedRank": {"current": 2}},
            ],
        }],
    }]}


def test_find_head_to_head_returns_event_when_opponent_present() -> None:
    event = pipeline._find_head_to_head(_schedule_with_h2h(), "41")
    assert event is not None
    assert pipeline._derive_game_context(event) == "Elite 8"


def test_find_head_to_head_returns_none_when_not_scheduled() -> None:
    assert pipeline._find_head_to_head(_schedule_with_h2h(), "999") is None


def test_scout_builds_context_with_neutral_fallback_when_no_game(monkeypatch) -> None:
    monkeypatch.setattr(pipeline, "fetch_team", lambda league, tid: _illinois_payload() if tid == "356" else _uconn_payload())
    monkeypatch.setattr(pipeline, "fetch_schedule", lambda league, tid, season=None: {"events": []})

    emitter = RecordingEmitter()
    ctx = pipeline._scout(NCAA, MatchupRequest("mens-college-basketball", "356", "41"), emitter)

    assert ctx.team_a.name == "Illinois"
    assert ctx.team_b.name == "UConn"
    assert ctx.head_to_head_event is None
    assert ctx.game_context == "NCAA Men's Basketball Matchup"
    # With no head-to-head event, ranks fall back to each team's standalone curated rank (spec §2.3)
    assert ctx.team_a.rank == 8
    assert ctx.team_b.rank == 5


def test_run_emits_done_when_scout_fails(monkeypatch) -> None:
    def boom(league, tid):
        raise RuntimeError("espn down")

    monkeypatch.setattr(pipeline, "fetch_team", boom)
    emitter = RecordingEmitter()

    pipeline.run(MatchupRequest("mens-college-basketball", "356", "41"), emitter)

    assert any(e["type"] == "agent_thought" and "Scout error" in e["content"] for e in emitter.events)
    assert emitter.events[-1] == {"type": "done"}


def test_run_calls_narrator_with_team_names(monkeypatch) -> None:
    monkeypatch.setattr(pipeline, "fetch_team", lambda league, tid: _illinois_payload() if tid == "356" else _uconn_payload())
    monkeypatch.setattr(pipeline, "fetch_schedule", lambda league, tid, season=None: _schedule_with_h2h())
    monkeypatch.setattr(pipeline, "converse_text", lambda prompt, max_tokens=1024: "summary")

    captured = {}

    def fake_run_narrator(scout_summary, analyst_summary, emit, team_header, stat_table, team_a_name, team_b_name):
        captured["names"] = (team_a_name, team_b_name)
        captured["header_keys"] = set(team_header)
        emit({"type": "prediction", "content": "Illinois 78-74"})

    monkeypatch.setattr(pipeline, "run_narrator", fake_run_narrator)
    emitter = RecordingEmitter()

    pipeline.run(MatchupRequest("mens-college-basketball", "356", "41"), emitter)

    assert captured["names"] == ("Illinois", "UConn")
    assert "team_a_name" in captured["header_keys"]
    assert emitter.events[-1] == {"type": "done"}
