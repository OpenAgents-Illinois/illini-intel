# Open-Domain Matchup Intelligence Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure the Illinois-basketball-specific pipeline into a general team-vs-team matchup engine for any ESPN league, using a `Matchup` domain object and symmetric `team_a`/`team_b` framing.

**Architecture:** A static `leagues` registry parameterizes ESPN's uniform site API by sport/league path. The Scout phase resolves a `MatchupRequest` (league + two team ids) into a `MatchupContext` (two `TeamRef`s, head-to-head event, stat table, recent form), which downstream phases consume. Every `illinois_*`/`opponent_*` SSE field and prompt becomes neutral `team_a`/`team_b`. The frontend swaps its free-text box for league + two-team selectors. The app defaults to Illinois vs UConn so existing behavior survives.

**Tech Stack:** Python 3.12, FastAPI, httpx, boto3 (Bedrock), pytest · vinext (Vite + React 19), Vitest.

**Spec:** `docs/superpowers/specs/2026-06-14-open-domain-matchup-intelligence-design.md`

---

## Conventions for this plan

- **Backend tests** run from the repo root: `uv run --project backend pytest <path> -v`
- **Frontend tests** run from `frontend/`: `npx vitest run <path>`
- Existing test style: backend uses `monkeypatch.setattr(module, "name", fake)` and a `RecordingEmitter` callable; frontend uses bare `test(...)` + `expect`.
- TDD throughout: write the failing test, watch it fail, implement minimally, watch it pass, commit.

## Setup (do once before Task 1)

- [ ] Create a feature branch off `master`:

```bash
git checkout -b feat/open-domain-matchup
```

---

## File Structure

**Backend — new:**
- `backend/app/core/leagues.py` — `League` dataclass + `LEAGUES` registry + `get_league`.
- `backend/app/models/matchup.py` — `TeamRef`, `MatchupRequest`, `MatchupContext`.

**Backend — modified:**
- `backend/app/core/config.py` — drop Illinois/UConn/ESPN-URL/DEFAULT_GOAL; add league + team defaults.
- `backend/app/clients/espn.py` — league-aware fetchers; add `fetch_teams`; remove `fetch_scoreboard`.
- `backend/app/models/events.py` — rename event fields to `team_a`/`team_b`; `report_card` gains `team`; `win_probability` → `team_a_probability`; remove `chart`.
- `backend/app/services/pipeline.py` — Scout rewrite around `MatchupRequest`/`MatchupContext`; delete goal-parsing heuristics.
- `backend/app/services/narrator.py` — symmetric prompts/fields; both-team report cards; new signature.
- `backend/app/api/routes.py` — `/analyze?league&team_a&team_b`, new `/leagues` and `/teams`.

**Frontend — modified:**
- `app/features/analysis/types.ts`, `state.ts` — field renames; remove `chart`/`charts`.
- `app/features/analysis/hooks/useAgentStream.ts` — structured selection → query string.
- `app/features/analysis/components/AnalysisPage.tsx` — selectors + de-branding.
- `components/{TeamHeader,WinProbability,StatComparisonChart,KeyFactors,ReportCardGrid,RecentForm,teamColors}.tsx/ts` — renames; WinProbability derives team_b.
- `components/GroupedBarChart.tsx` — deleted (dead chart plumbing).
- `__tests__/*` — updated assertions.

---

## Chunk 1: Backend domain foundation

### Task 1: League registry

**Files:**
- Create: `backend/app/core/leagues.py`
- Test: `backend/tests/test_leagues.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_leagues.py
from __future__ import annotations

from app.core import leagues


def test_get_league_returns_known_league() -> None:
    league = leagues.get_league("nba")
    assert league is not None
    assert league.sport == "basketball"
    assert league.path == "basketball/nba"
    assert league.label == "NBA"


def test_get_league_returns_none_for_unknown_key() -> None:
    assert leagues.get_league("quidditch") is None


def test_every_registry_entry_is_well_formed() -> None:
    for key, league in leagues.LEAGUES.items():
        assert league.key == key
        assert league.sport
        assert league.path.startswith(f"{league.sport}/")
        assert league.label


def test_default_league_is_registered() -> None:
    assert "mens-college-basketball" in leagues.LEAGUES
```

- [ ] **Step 2: Run it, expect failure**

Run: `uv run --project backend pytest backend/tests/test_leagues.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.core.leagues'`.

- [ ] **Step 3: Implement**

```python
# backend/app/core/leagues.py
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
```

- [ ] **Step 4: Run it, expect pass**

Run: `uv run --project backend pytest backend/tests/test_leagues.py -v` → PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/leagues.py backend/tests/test_leagues.py
git commit -m "feat(core): add ESPN league registry"
```

---

### Task 2: Matchup domain models

**Files:**
- Create: `backend/app/models/matchup.py`
- Test: `backend/tests/test_matchup.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_matchup.py
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
```

- [ ] **Step 2: Run it, expect failure** (`No module named 'app.models.matchup'`).

Run: `uv run --project backend pytest backend/tests/test_matchup.py -v`

- [ ] **Step 3: Implement**

```python
# backend/app/models/matchup.py
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
```

- [ ] **Step 4: Run it, expect pass.**

- [ ] **Step 5: Commit**

```bash
git add backend/app/models/matchup.py backend/tests/test_matchup.py
git commit -m "feat(models): add Matchup domain model"
```

---

### Task 3: League-aware ESPN client

**Files:**
- Modify: `backend/app/clients/espn.py`
- Test: `backend/tests/test_espn.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_espn.py
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
        return FakeResponse({"sports": []})

    monkeypatch.setattr(espn.httpx, "get", fake_get)
    espn.fetch_teams(get_league("nfl"))

    assert seen["url"].endswith("/football/nfl/teams")


def test_fetch_scoreboard_removed() -> None:
    assert not hasattr(espn, "fetch_scoreboard")
```

- [ ] **Step 2: Run it, expect failure** (signature mismatch / `fetch_team` takes a string today).

Run: `uv run --project backend pytest backend/tests/test_espn.py -v`

- [ ] **Step 3: Implement** — replace the whole file:

```python
# backend/app/clients/espn.py
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
    return _get_json(league, "/teams", timeout=timeout)
```

- [ ] **Step 4: Run it, expect pass.**

- [ ] **Step 5: Commit**

```bash
git add backend/app/clients/espn.py backend/tests/test_espn.py
git commit -m "feat(clients): make ESPN client league-aware, add fetch_teams"
```

---

### Task 4: Config cleanup

**Files:**
- Modify: `backend/app/core/config.py`
- Test: `backend/tests/test_config.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_config.py
from __future__ import annotations

from app.core import config


def test_matchup_defaults_present() -> None:
    assert config.DEFAULT_LEAGUE == "mens-college-basketball"
    assert config.DEFAULT_TEAM_A == "356"   # Illinois
    assert config.DEFAULT_TEAM_B == "41"    # UConn


def test_legacy_constants_removed() -> None:
    for name in ("ILLINOIS_TEAM_ID", "UCONN_TEAM_ID", "ESPN_BASE_URL", "DEFAULT_GOAL"):
        assert not hasattr(config, name), f"{name} should be removed"
```

- [ ] **Step 2: Run it, expect failure.**

Run: `uv run --project backend pytest backend/tests/test_config.py -v`

- [ ] **Step 3: Implement** — replace the whole file:

```python
# backend/app/core/config.py
from __future__ import annotations

import os

AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
BEDROCK_MODEL_ID = os.environ.get(
    "BEDROCK_MODEL_ID", "us.meta.llama3-3-70b-instruct-v1:0"
)
DEFAULT_LEAGUE = os.environ.get("DEFAULT_LEAGUE", "mens-college-basketball")
DEFAULT_TEAM_A = os.environ.get("DEFAULT_TEAM_A", "356")  # Illinois
DEFAULT_TEAM_B = os.environ.get("DEFAULT_TEAM_B", "41")   # UConn
```

- [ ] **Step 4: Run it, expect pass.**

> NOTE: After this task the existing `pipeline.py`, `narrator.py`, `routes.py` will not import (they reference removed names). That is expected — Tasks 5–8 rewrite them. Do not run the full suite until the end of Chunk 2. Each task below still runs and commits its own targeted tests.

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/config.py backend/tests/test_config.py
git commit -m "refactor(config): drop Illinois-specific constants, add matchup defaults"
```

---

## Chunk 2: Events, pipeline, narrator

### Task 5: Rename the SSE event contract

**Files:**
- Modify: `backend/app/models/events.py`
- Test: `backend/tests/test_events.py` (rewrite existing assertions)

- [ ] **Step 1: Rewrite the failing tests**

```python
# backend/tests/test_events.py
from app.models import events


def test_team_header_event_uses_team_a_team_b_fields() -> None:
    event = events.team_header(
        3, "Illinois", "Fighting Illini", "UConn", "Huskies", 2, "Final Four",
        team_a_color="ff5f05", team_b_color="0c2340",
    )
    assert event == {
        "type": "team_header",
        "team_a_rank": 3,
        "team_a_name": "Illinois",
        "team_a_mascot": "Fighting Illini",
        "team_a_color": "ff5f05",
        "team_b_name": "UConn",
        "team_b_mascot": "Huskies",
        "team_b_rank": 2,
        "team_b_color": "0c2340",
        "game_context": "Final Four",
    }


def test_stat_comparison_event_uses_team_a_team_b_fields() -> None:
    assert events.stat_comparison("Tempo", "73.1", "69.4", 0.57) == {
        "type": "stat_comparison",
        "label": "Tempo",
        "team_a_value": "73.1",
        "team_b_value": "69.4",
        "team_a_pct": 0.57,
    }


def test_report_card_event_carries_team_tag() -> None:
    assert events.report_card("team_b", "Defense", "A-", "0.42 OppFG%", "Locks down") == {
        "type": "report_card",
        "team": "team_b",
        "dimension": "Defense",
        "grade": "A-",
        "stat": "0.42 OppFG%",
        "explanation": "Locks down",
    }


def test_win_probability_event_is_team_a_probability() -> None:
    assert events.win_probability(61.0) == {
        "type": "win_probability",
        "team_a_probability": 61.0,
    }


def test_key_factor_favors_team_side() -> None:
    assert events.key_factor("Rebounding Edge", "Wins the glass", "team_a") == {
        "type": "key_factor",
        "label": "Rebounding Edge",
        "detail": "Wins the glass",
        "favors": "team_a",
    }


def test_chart_event_removed() -> None:
    assert not hasattr(events, "chart")


def test_done_event_is_terminal_marker() -> None:
    assert events.done() == {"type": "done"}
```

- [ ] **Step 2: Run it, expect failure.**

Run: `uv run --project backend pytest backend/tests/test_events.py -v`

- [ ] **Step 3: Implement** — edit `events.py`: replace `team_header`, `stat_comparison`, `report_card`, `win_probability`, `key_factor`; delete `chart`. Keep `agent_thought`, `tool_call`, `tool_result`, `insight_card`, `matchup_preview`, `prediction`, `recent_form`, `done` as-is.

```python
def team_header(
    team_a_rank: int | None,
    team_a_name: str,
    team_a_mascot: str,
    team_b_name: str,
    team_b_mascot: str,
    team_b_rank: int | None,
    game_context: str,
    team_a_color: str | None = None,
    team_b_color: str | None = None,
) -> dict[str, Any]:
    return {
        "type": "team_header",
        "team_a_rank": team_a_rank,
        "team_a_name": team_a_name,
        "team_a_mascot": team_a_mascot,
        "team_a_color": team_a_color,
        "team_b_name": team_b_name,
        "team_b_mascot": team_b_mascot,
        "team_b_rank": team_b_rank,
        "team_b_color": team_b_color,
        "game_context": game_context,
    }


def stat_comparison(label: str, team_a_value: str, team_b_value: str, team_a_pct: float) -> dict[str, Any]:
    return {
        "type": "stat_comparison",
        "label": label,
        "team_a_value": team_a_value,
        "team_b_value": team_b_value,
        "team_a_pct": team_a_pct,
    }


def report_card(team: str, dimension: str, grade: str, stat: str, explanation: str) -> dict[str, Any]:
    return {
        "type": "report_card",
        "team": team,
        "dimension": dimension,
        "grade": grade,
        "stat": stat,
        "explanation": explanation,
    }


def win_probability(team_a_probability: float) -> dict[str, Any]:
    return {"type": "win_probability", "team_a_probability": team_a_probability}


def key_factor(label: str, detail: str, favors: str) -> dict[str, Any]:
    return {"type": "key_factor", "label": label, "detail": detail, "favors": favors}
```

- [ ] **Step 4: Run it, expect pass.**

- [ ] **Step 5: Commit**

```bash
git add backend/app/models/events.py backend/tests/test_events.py
git commit -m "feat(events): symmetric team_a/team_b contract, drop chart event"
```

---

### Task 6: Scout phase rewrite (pipeline)

**Files:**
- Modify: `backend/app/services/pipeline.py` (near-rewrite)
- Test: `backend/tests/test_pipeline.py` (rewrite)

Helper map for this task:
- **Delete:** `_resolve_matchup_event`, `_event_match_score`, `_event_labels`, `_candidate_seasons`, `_extract_goal_years`, `ROUND_KEYWORDS`, `_opponent_competitor`, `_opponent_team_id`, `_build_team_header`, `_team_display_fields`.
- **Keep (drop Illinois defaults only):** `_coerce_rank`, `_extract_competitor`, `_extract_ap_rank`, `_season_from_date`, `_competitors_from_event`, `_competitor_for_team`, `_derive_game_context`, `_rank_from_event`, `_extract_recent_form`, `_slim_team`, `_extract_stat_map`, `_build_stat_comparison_table` (rename its row keys to `team_a`/`team_b`).
- **Add:** `_team_ref(league, team_payload, team_id, event)`, `_find_head_to_head(schedule, opponent_id)`, `_scout(league, request, emit) -> MatchupContext`, and a rewritten `run(request, emit)`.

- [ ] **Step 1: Write the failing tests**

```python
# backend/tests/test_pipeline.py
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
    return {"team": {"id": "356", "shortDisplayName": "Illinois", "name": "Fighting Illini", "color": "ff5f05"}}


def _uconn_payload():
    return {"team": {"id": "41", "shortDisplayName": "UConn", "name": "Huskies", "color": "0c2340"}}


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
```

- [ ] **Step 2: Run it, expect failure.**

Run: `uv run --project backend pytest backend/tests/test_pipeline.py -v`

- [ ] **Step 3: Implement** — rewrite `pipeline.py`. Keep the retained helpers (copy them forward, changing only `fetch_*` calls to take `league` and `_build_stat_comparison_table` row keys to `team_a`/`team_b`). Replace the Scout/`run` section with:

```python
def _team_ref(league, team_payload: dict, team_id: str, event: dict | None) -> "TeamRef":
    team = team_payload.get("team", {})
    name = team.get("shortDisplayName") or team.get("displayName") or team.get("location") or "Team"
    mascot = team.get("name") or team.get("nickname") or ""
    color = team.get("color")
    rank = _rank_from_event(event, team_id) if event else _extract_ap_rank(team_payload, team_id)
    return TeamRef(id=str(team_id), name=name, mascot=mascot, color=color, rank=rank)


def _find_head_to_head(schedule: dict, opponent_id: str) -> dict | None:
    for event in schedule.get("events", []):
        if not isinstance(event, dict):
            continue
        for competitor in _competitors_from_event(event):
            if str(competitor.get("team", {}).get("id")) == str(opponent_id):
                return event
    return None


def _team_header_dict(ctx: "MatchupContext") -> dict:
    return {
        "team_a_rank": ctx.team_a.rank,
        "team_a_name": ctx.team_a.name,
        "team_a_mascot": ctx.team_a.mascot,
        "team_a_color": ctx.team_a.color,
        "team_b_rank": ctx.team_b.rank,
        "team_b_name": ctx.team_b.name,
        "team_b_mascot": ctx.team_b.mascot,
        "team_b_color": ctx.team_b.color,
        "game_context": ctx.game_context,
    }


def _scout(league, request: "MatchupRequest", emit: Emitter) -> "MatchupContext":
    emit(events.tool_call("scout", "fetch_team", {"team_id": request.team_a_id}))
    team_a_payload = fetch_team(league, request.team_a_id)
    emit(events.tool_result("scout", "fetch_team", {"team": team_a_payload.get("team", {}).get("displayName", "Team A")}))

    emit(events.tool_call("scout", "fetch_team", {"team_id": request.team_b_id}))
    team_b_payload = fetch_team(league, request.team_b_id)
    emit(events.tool_result("scout", "fetch_team", {"team": team_b_payload.get("team", {}).get("displayName", "Team B")}))

    season = _season_from_date()
    emit(events.tool_call("scout", "fetch_schedule", {"team_id": request.team_a_id, "season": season}))
    schedule_a = fetch_schedule(league, request.team_a_id, season=season)
    emit(events.tool_result("scout", "fetch_schedule", {"team": "team_a", "games": len(schedule_a.get("events", []))}))

    emit(events.tool_call("scout", "fetch_schedule", {"team_id": request.team_b_id, "season": season}))
    schedule_b = fetch_schedule(league, request.team_b_id, season=season)
    emit(events.tool_result("scout", "fetch_schedule", {"team": "team_b", "games": len(schedule_b.get("events", []))}))

    h2h = _find_head_to_head(schedule_a, request.team_b_id)
    game_context = _derive_game_context(h2h) or f"{league.label} Matchup"

    team_a = _team_ref(league, team_a_payload, request.team_a_id, h2h)
    team_b = _team_ref(league, team_b_payload, request.team_b_id, h2h)
    stat_table = _build_stat_comparison_table(team_a_payload, team_b_payload)

    ctx = MatchupContext(
        league=league,
        team_a=team_a,
        team_b=team_b,
        head_to_head_event=h2h,
        game_context=game_context,
        stat_table=stat_table,
        team_a_form=_extract_recent_form(schedule_a, request.team_a_id),
        team_b_form=_extract_recent_form(schedule_b, request.team_b_id),
    )
    emit(events.recent_form(team_a.name, ctx.team_a_form))
    emit(events.recent_form(team_b.name, ctx.team_b_form))
    return ctx


def _scout_summary(ctx: "MatchupContext") -> str:
    raw_context = {
        "team_a": _slim_team_by_name(ctx.team_a),
        "team_b": _slim_team_by_name(ctx.team_b),
        "stat_comparison_table": ctx.stat_table,
    }
    prompt = (
        f"You are the Scout agent for a {ctx.league.sport} matchup between "
        f"{ctx.team_a.name} and {ctx.team_b.name}. Review this ESPN-derived context and write a "
        "concise scouting summary for downstream analysis. The stat_comparison_table contains "
        f"side-by-side season averages for both teams — explicitly mention key stats for BOTH "
        "teams by name. Plain text only.\n\n"
        f"Context:\n{json.dumps(raw_context, default=str)[:12000]}"
    )
    return converse_text(prompt, max_tokens=900)


def run(request: "MatchupRequest", emit: Emitter) -> None:
    league = get_league(request.league_key)
    if league is None:
        emit(events.agent_thought("scout", f"Unknown league: {request.league_key!r}"))
        emit(events.done())
        return

    emit(events.agent_thought("scout", f"Scouting {league.label}: {request.team_a_id} vs {request.team_b_id}"))
    scout_summary = ""
    ctx = None
    try:
        ctx = _scout(league, request, emit)
        scout_summary = _scout_summary(ctx)
    except Exception as error:
        scout_summary = "Scout error"
        emit(events.agent_thought("scout", f"Scout error: {error!r}"))

    emit(events.agent_thought("analyst", "Starting analyst agent"))
    analyst_summary = ""
    if scout_summary == "Scout error":
        analyst_summary = "Analyst error"
        emit(events.agent_thought("analyst", "Analyst skipped because scout failed."))
    else:
        try:
            prompt = (
                f"Scout summary:\n{scout_summary}\n\n"
                f"You are the analyst for {ctx.team_a.name} vs {ctx.team_b.name}. Produce a concise "
                "analysis covering matchup dynamics, risk factors, and 4-6 concrete takeaways. Plain text."
            )
            analyst_summary = converse_text(prompt, max_tokens=900)
        except Exception as error:
            analyst_summary = "Analyst error"
            emit(events.agent_thought("analyst", f"Analyst error: {error!r}"))

    if scout_summary == "Scout error" or analyst_summary == "Analyst error":
        emit(events.agent_thought("narrator", "Skipping narrator because upstream agents failed."))
    else:
        try:
            run_narrator(
                scout_summary,
                analyst_summary,
                emit,
                team_header=_team_header_dict(ctx),
                stat_table=ctx.stat_table,
                team_a_name=ctx.team_a.name,
                team_b_name=ctx.team_b.name,
            )
        except Exception as error:
            emit(events.agent_thought("narrator", f"Narrator error: {error!r}"))

    emit(events.done())
```

Also add a small helper `_slim_team_by_name(team_ref)` returning `{"name": ref.name, "mascot": ref.mascot, "rank": ref.rank}`, update imports (`from app.core.leagues import get_league`, `from app.models.matchup import MatchupContext, MatchupRequest, TeamRef`), drop `ILLINOIS_TEAM_ID`/`UCONN_TEAM_ID` imports, and change `_build_stat_comparison_table` to emit rows `{"stat": k, "team_a": ..., "team_b": ...}`.

- [ ] **Step 4: Run it, expect pass.**

Run: `uv run --project backend pytest backend/tests/test_pipeline.py -v`

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/pipeline.py backend/tests/test_pipeline.py
git commit -m "feat(pipeline): resolve MatchupContext deterministically, drop goal heuristics"
```

---

### Task 7: Narrator symmetric rewrite

**Files:**
- Modify: `backend/app/services/narrator.py`
- Test: `backend/tests/test_narrator_stats.py`, `test_narrator_json.py`, `test_narrator_prediction.py` (rename fields)

- [ ] **Step 1: Update the failing tests** — in all three narrator test files, replace `illinois_value`→`team_a_value`, `opponent_value`→`team_b_value`, `illinois_pct`→`team_a_pct`. Add to `test_narrator_stats.py`:

```python
def test_run_narrator_emits_win_probability_with_team_a_field(monkeypatch) -> None:
    from app.services import narrator

    monkeypatch.setattr(narrator, "generate_insight_card", lambda c: {"title": "t", "data": {}})
    monkeypatch.setattr(narrator, "generate_team_header", lambda c: {})
    monkeypatch.setattr(narrator, "generate_win_probability", lambda c: 61.0)
    monkeypatch.setattr(narrator, "generate_stat_comparisons", lambda c, t=None: [])
    monkeypatch.setattr(narrator, "generate_report_cards", lambda c, t=None: [
        {"team": "team_a", "dimension": "Scoring", "grade": "A", "stat": "80.0", "explanation": "x"},
        {"team": "team_b", "dimension": "Defense", "grade": "B", "stat": "0.42", "explanation": "y"},
    ])
    monkeypatch.setattr(narrator, "generate_key_factors", lambda c: [])
    monkeypatch.setattr(narrator, "generate_matchup_preview", lambda c: "preview")
    monkeypatch.setattr(narrator, "generate_prediction", lambda c, wp: "pred")

    seen = []
    narrator.run_narrator("scout", "analyst", seen.append,
                          team_header={"team_a_name": "Illinois", "team_b_name": "UConn"},
                          stat_table=[], team_a_name="Illinois", team_b_name="UConn")

    win = [e for e in seen if e["type"] == "win_probability"][0]
    assert win == {"type": "win_probability", "team_a_probability": 61.0}
    cards = [e for e in seen if e["type"] == "report_card"]
    assert {c["team"] for c in cards} == {"team_a", "team_b"}
```

- [ ] **Step 2: Run it, expect failure.**

Run: `uv run --project backend pytest backend/tests/test_narrator_stats.py backend/tests/test_narrator_json.py backend/tests/test_narrator_prediction.py -v`

- [ ] **Step 3: Implement** narrator changes:
  - `run_narrator` signature → `run_narrator(scout_summary, analyst_summary, emit, team_header, stat_table, team_a_name, team_b_name)`. Build `context` from the summaries + a `FACTUAL ESPN STATS` block from `stat_table` (rows now keyed `team_a`/`team_b`), and prepend a line naming the two teams. Remove the old `goal` param.
  - `_normalize_stat_comparison_items`: rename `illinois_value`/`opponent_value`/`illinois_pct` → `team_a_value`/`team_b_value`/`team_a_pct`. Update `generate_stat_comparisons` prompt to compute `team_a_pct = team_a / (team_a + team_b)` and emit `team_a_value`/`team_b_value`.
  - `generate_report_cards`: prompt now grades BOTH teams; each item must include `"team": "team_a"|"team_b"`. Keep the null-stat filter; also drop any item whose `team` is not `team_a`/`team_b`.
  - `generate_win_probability`: unchanged math; it returns P(team_a). Emit via `events.win_probability(value)` (single field).
  - `generate_team_header`: prompt returns neutral `team_a_*`/`team_b_*` keys; `_merge_team_header` renames its key lists to `team_a_*`/`team_b_*`.
  - `generate_key_factors`: `favors` allowed values become `team_a`/`team_b` (drop `neutral`; default the odd one out to `team_a`). Prompt: "Every factor must clearly favor team_a or team_b."
  - `generate_charts` and any `events.chart` usage: **delete**.
  - Emit loop: `events.stat_comparison(label, team_a_value, team_b_value, team_a_pct)`; `events.report_card(item["team"], dimension, grade, stat, explanation)`; `events.win_probability(win_probability)`.
  - In every prompt string, replace "Illinois"/"the Illini" with `{team_a_name}` and "opponent" with `{team_b_name}`.

- [ ] **Step 4: Run it, expect pass.**

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/narrator.py backend/tests/test_narrator_*.py
git commit -m "feat(narrator): symmetric team_a/team_b BI, grade both teams, single win prob"
```

---

## Chunk 3: API and frontend

### Task 8: API surface

**Files:**
- Modify: `backend/app/api/routes.py`
- Test: `backend/tests/test_api.py` (rewrite)

- [ ] **Step 1: Rewrite the failing tests**

```python
# backend/tests/test_api.py
from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint_returns_ok() -> None:
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.text == "ok"


def test_leagues_endpoint_lists_registry() -> None:
    response = TestClient(app).get("/leagues")
    assert response.status_code == 200
    keys = {item["key"] for item in response.json()}
    assert {"mens-college-basketball", "nba"} <= keys


def test_analyze_passes_structured_request(monkeypatch) -> None:
    seen = {}

    def fake_run_pipeline(request, emit):
        seen["req"] = request
        emit({"type": "done"})

    monkeypatch.setattr("app.api.routes.run_pipeline", fake_run_pipeline)
    response = TestClient(app).get("/analyze", params={"league": "nba", "team_a": "13", "team_b": "2"})

    assert response.status_code == 200
    assert (seen["req"].league_key, seen["req"].team_a_id, seen["req"].team_b_id) == ("nba", "13", "2")
    assert '"type": "done"' in response.text


def test_analyze_defaults_to_illini_matchup(monkeypatch) -> None:
    seen = {}

    def fake_run_pipeline(request, emit):
        seen["req"] = request
        emit({"type": "done"})

    monkeypatch.setattr("app.api.routes.run_pipeline", fake_run_pipeline)
    TestClient(app).get("/analyze")

    assert (seen["req"].league_key, seen["req"].team_a_id, seen["req"].team_b_id) == (
        "mens-college-basketball", "356", "41",
    )


def test_analyze_rejects_equal_teams() -> None:
    response = TestClient(app).get("/analyze", params={"league": "nba", "team_a": "13", "team_b": "13"})
    assert response.status_code == 200
    assert "must be different" in response.text
    assert '"type": "done"' in response.text


def test_teams_endpoint_returns_options(monkeypatch) -> None:
    def fake_fetch_teams(league):
        return {"sports": [{"leagues": [{"teams": [
            {"team": {"id": "13", "displayName": "Los Angeles Lakers"}},
            {"team": {"id": "2", "displayName": "Boston Celtics"}},
        ]}]}]}

    monkeypatch.setattr("app.api.routes.fetch_teams", fake_fetch_teams)
    response = TestClient(app).get("/teams", params={"league": "nba"})

    assert response.status_code == 200
    assert {"id": "13", "name": "Los Angeles Lakers"} in response.json()
```

- [ ] **Step 2: Run it, expect failure.**

Run: `uv run --project backend pytest backend/tests/test_api.py -v`

- [ ] **Step 3: Implement** — rewrite `routes.py`:

```python
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


@router.get("/teams")
async def teams(league: str = Query(...)) -> JSONResponse:
    resolved = get_league(league)
    if resolved is None:
        return JSONResponse([], status_code=200)
    payload = await asyncio.to_thread(fetch_teams, resolved)
    options = _extract_team_options(payload)
    return JSONResponse(options)


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
```

- [ ] **Step 4: Run it, expect pass.**

- [ ] **Step 5: Run the FULL backend suite — everything must be green now.**

Run: `uv run --project backend pytest backend/tests -v`
Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add backend/app/api/routes.py backend/tests/test_api.py
git commit -m "feat(api): structured /analyze + /leagues + /teams endpoints"
```

---

### Task 9: Frontend types & state rename

**Files:**
- Modify: `frontend/app/features/analysis/types.ts`, `state.ts`
- Test: `frontend/app/features/analysis/__tests__/state.test.ts` (rewrite), `statComparison.test.ts`, `predictionText.test.ts` (rename fields)

- [ ] **Step 1: Rewrite `state.test.ts`** to use `team_a_*`/`team_b_*`:

```ts
import { applyEvent, initialStreamState } from "../state";

test("team_header event populates teamHeader with team_a/team_b", () => {
  const event = {
    type: "team_header" as const,
    team_a_rank: 3, team_a_name: "Illinois", team_a_mascot: "Fighting Illini",
    team_b_name: "UConn", team_b_mascot: "Huskies", team_b_rank: 1,
    game_context: "Final Four",
  };
  const next = applyEvent(initialStreamState, event);
  expect(next.teamHeader?.team_a_name).toBe("Illinois");
  expect(next.teamHeader?.team_b_name).toBe("UConn");
});

test("stat_comparison appends with team_a/team_b values", () => {
  const event = {
    type: "stat_comparison" as const,
    label: "PPG", team_a_value: "87.3", team_b_value: "79.1", team_a_pct: 0.52,
  };
  const next = applyEvent(initialStreamState, event);
  expect(next.statComparisons[0].team_a_value).toBe("87.3");
});

test("report_card carries team tag", () => {
  const event = {
    type: "report_card" as const,
    team: "team_b" as const, dimension: "Defense", grade: "A-", stat: "x", explanation: "y",
  };
  const next = applyEvent(initialStreamState, event);
  expect(next.reportCards[0].team).toBe("team_b");
});

test("win_probability sets winProbability from team_a_probability", () => {
  const next = applyEvent(initialStreamState, { type: "win_probability" as const, team_a_probability: 61 });
  expect(next.winProbability).toBe(61);
});
```

- [ ] **Step 2: Run it, expect failure.**

Run (from `frontend/`): `npx vitest run app/features/analysis/__tests__/state.test.ts`

- [ ] **Step 3: Implement** — in `types.ts`: rename the `team_header`, `stat_comparison`, `report_card`, `win_probability`, `key_factor` members of `AgentEvent` and the matching `*Item`/`*Data` interfaces to `team_a_*`/`team_b_*` (report card gains `team: "team_a" | "team_b"`; win prob field `team_a_probability`). Remove `ChartItem`, `ChartSeriesItem`, the `chart` event member, and `charts` from `StreamState`. In `state.ts`: rewrite `normalizeTeamHeader` to map the new fields with neutral defaults (`team_a_name ?? "Team A"`, `team_b_name ?? "Team B"`, `game_context ?? "Matchup"`); update each `applyEvent` case to the new field names; set `winProbability` from `event.team_a_probability`; delete the `chart` case and `charts` from `initialStreamState`.

- [ ] **Step 4: Run state + statComparison + predictionText tests, expect pass.**

Run (from `frontend/`): `npx vitest run app/features/analysis/__tests__/`

- [ ] **Step 5: Commit**

```bash
git add frontend/app/features/analysis/types.ts frontend/app/features/analysis/state.ts frontend/app/features/analysis/__tests__/
git commit -m "feat(frontend): rename stream state to team_a/team_b, drop charts"
```

---

### Task 10: Selectors & stream hook

**Files:**
- Modify: `frontend/app/features/analysis/hooks/useAgentStream.ts`, `components/AnalysisPage.tsx`
- Create: `components/MatchupSelector.tsx`

- [ ] **Step 1: Implement `useAgentStream.start`** to accept `{ league, teamA, teamB }` and build the URL:

```ts
const start = useCallback((selection: { league: string; teamA: string; teamB: string }) => {
  // ...reset state as today...
  const base = process.env.NEXT_PUBLIC_API_GATEWAY_URL ?? "";
  const url =
    `${base}/analyze?league=${encodeURIComponent(selection.league)}` +
    `&team_a=${encodeURIComponent(selection.teamA)}` +
    `&team_b=${encodeURIComponent(selection.teamB)}`;
  const eventSource = new EventSource(url);
  // ...rest unchanged...
}, [onStateChange]);
```

- [ ] **Step 2: Create `MatchupSelector.tsx`** — a client component that:
  - On mount, fetches `${base}/leagues` → league `<select>` (default `mens-college-basketball`).
  - When league changes, fetches `${base}/teams?league=<key>` → populates Team A and Team B `<select>`s and **resets** both selections.
  - Defaults: when the league is `mens-college-basketball` and options include id `356`/`41`, preselect Team A=356, Team B=41.
  - Team A options exclude the current Team B id; Team B options exclude the current Team A id (symmetric).
  - Exposes the chosen `{ league, teamA, teamB }` upward and a disabled state while running.

- [ ] **Step 3: Rewire `AnalysisPage.tsx`** — replace the single text input with `<MatchupSelector>`; "Run Analysis" calls `start({ league, teamA, teamB })` when not running and both teams are chosen; change the header text from "Illini Intel / Fighting Illini Basketball BI" to "Matchup Intel"; swap the orange focus/button classes for a neutral accent (e.g. `indigo`/`zinc`). Remove the old `DEFAULT_GOAL` constant.

- [ ] **Step 4: Verify build (no test for wiring).**

Run (from `frontend/`): `npm run build`
Expected: build succeeds.

- [ ] **Step 5: Commit**

```bash
git add frontend/app/features/analysis/hooks/useAgentStream.ts frontend/app/features/analysis/components/AnalysisPage.tsx frontend/app/features/analysis/components/MatchupSelector.tsx
git commit -m "feat(frontend): league + two-team selectors replace goal text box"
```

---

### Task 11: Component renames + colors + dead chart removal

**Files:**
- Modify: `components/TeamHeader.tsx`, `WinProbability.tsx`, `StatComparisonChart.tsx`, `statComparison.ts`, `KeyFactors.tsx`, `ReportCardGrid.tsx`, `RecentForm.tsx`, `BiReportPanel.tsx`, `teamColors.ts`
- Delete: `components/GroupedBarChart.tsx`
- Test: `__tests__/statComparison.test.ts` (already renamed in Task 9), add a `WinProbability` derivation test

- [ ] **Step 1: Add a failing WinProbability test** (`__tests__/winProbability.test.ts`):

```ts
import { teamBProbability } from "../components/WinProbability";

test("derives team_b probability as 100 - team_a", () => {
  expect(teamBProbability(61)).toBeCloseTo(39);
  expect(teamBProbability(0)).toBeCloseTo(100);
});
```

- [ ] **Step 2: Run it, expect failure** (export missing).

Run (from `frontend/`): `npx vitest run app/features/analysis/__tests__/winProbability.test.ts`

- [ ] **Step 3: Implement renames**:
  - `WinProbability.tsx`: read `team_a_probability` via state, export `export const teamBProbability = (a: number) => 100 - a;`, render both sides using `team_a_name`/`team_b_name` and their colors.
  - `TeamHeader.tsx`: render `team_a_*` on the left, `team_b_*` on the right; ranks/colors/mascots from the renamed fields; the left side is no longer hardcoded orange/Illinois — use `teamColors` from each team's hex.
  - `StatComparisonChart.tsx` + `statComparison.ts`: rename `illinois_*`/`opponent_*` → `team_a_*`/`team_b_*`; bar share uses `team_a_pct`.
  - `KeyFactors.tsx`: `favors === "team_a"` / `"team_b"` styling (drop the `neutral`/`illinois`/`opponent` branches).
  - `ReportCardGrid.tsx`: group cards by `team` (a `team_a` column/section and a `team_b` one).
  - `RecentForm.tsx`: unchanged data (keyed by team name) — verify it still compiles.
  - `teamColors.ts`: keep `getColorsForTeam(name?: string, espnHex?: string)` that prefers the ESPN hex and falls back to a single neutral default; drop the per-school `TEAM_COLOR_MAP` and the `getIllinoisColors`/`getOpponentColors` Illinois-specific exports (replace call sites).
  - `BiReportPanel.tsx`: remove any `charts`/`GroupedBarChart` usage; render the renamed components.
  - Delete `GroupedBarChart.tsx`.

- [ ] **Step 4: Run the full frontend suite + build, expect pass.**

Run (from `frontend/`): `npx vitest run` then `npm run build`
Expected: all tests pass; build succeeds.

- [ ] **Step 5: Commit**

```bash
git add frontend/app/features/analysis/components/ frontend/app/features/analysis/__tests__/
git rm frontend/app/features/analysis/components/GroupedBarChart.tsx
git commit -m "feat(frontend): symmetric team_a/team_b components, ESPN colors, remove dead chart"
```

---

## Final verification

- [ ] **Backend:** `uv run --project backend pytest backend/tests -v` → all green.
- [ ] **Backend compiles:** `uv run --project backend python -m compileall backend/app backend/tests` → no errors.
- [ ] **Frontend tests:** from `frontend/`, `npx vitest run` → all green.
- [ ] **Frontend build:** from `frontend/`, `npm run build` → succeeds.
- [ ] **Manual smoke (optional, needs AWS creds):** `docker compose up --build`, open `http://localhost:3000`, confirm the default Illinois-vs-UConn report streams, then switch the league to NBA and pick two teams and confirm a report renders.
- [ ] **Finish the branch** using superpowers:finishing-a-development-branch.

## Notes on docs drift (out of scope, per spec)

`CLAUDE.md` and `README.md` still describe "Fighting Illini" framing and old event fields. Per the spec these are intentionally not rewritten in this plan. Refreshing the `## Event contract` section of `CLAUDE.md` is a cheap optional follow-up.
