# Illini Intel — Open-Domain Matchup Intelligence Design

**Date:** 2026-06-14
**Scope:** Restructure the Illinois-basketball-specific pipeline into a general team-vs-team matchup engine that works for any sport/league ESPN covers.

---

## Goal

Today the pipeline is hardwired to one sport (ESPN `mens-college-basketball`) and one team (Illinois, with UConn as a fallback opponent). The goal is to make it **open-domain**: a user picks any league and any two teams, and the same Scout → Analyst → Narrator pipeline produces a streamed BI report for that matchup.

The data source stays ESPN — its public site API has a uniform JSON shape across sports, so "open domain" is achieved by **parameterizing the sport/league path and the two team IDs**, not by adding new providers.

---

## Decisions (locked during brainstorming)

1. **Single data source, parameterized.** ESPN remains the only source. Sport/league and both team IDs become runtime parameters. No provider abstraction.
2. **Structured matchup input.** The user explicitly selects a league and two teams (dropdowns populated from ESPN), rather than free-text that gets parsed. The brittle goal-string opponent-resolution heuristic is removed.
3. **Symmetric `team_a` / `team_b` framing.** There is no privileged "home" team. Every Illinois-centric field/prompt becomes neutral team_a/team_b. Win probability is P(team_a wins); report cards grade **both** teams; key factors favor `team_a`/`team_b`.
4. **Approach B — `Matchup` domain object.** A single resolved context object is threaded through the pipeline instead of loose parameters, so "team_a vs team_b" is defined once.
5. **Clean break, no back-compat.** No external consumers exist; old field names are deleted rather than shimmed.
6. **Illini default preserved.** The app opens on, and a param-less `/analyze` resolves to, **Illinois (team_a) vs UConn (team_b)** in NCAA men's basketball.
7. **Internal-only generalization.** Repo name, Python package name, and `docs/` are unchanged. Only the user-facing frontend header is de-branded.

---

## Architecture

```text
Frontend (vinext)
  league + team selectors  ──GET /leagues, /teams──►  FastAPI
        |                                                  |
        | EventSource: /analyze?league&team_a&team_b       |
        v                                                  v
   stream renderer  ◄────────── SSE events ────────  pipeline.run(MatchupRequest)
                                                           |
                                            ┌──────────────┼───────────────┐
                                         ESPN client   leagues registry   narrator
                                       (league-aware)                  (team_a/team_b)
```

---

## Section 1 — Core domain model & league registry

### `backend/app/core/leagues.py` (new)

A static registry — the **only** place a sport/league is enumerated. Adding a league is one line.

```python
@dataclass(frozen=True)
class League:
    key: str        # e.g. "nba"
    sport: str      # e.g. "basketball"
    path: str       # ESPN path segment, e.g. "basketball/nba"
    label: str      # display, e.g. "NBA"

LEAGUES: dict[str, League] = {
    "mens-college-basketball": League("mens-college-basketball", "basketball",
        "basketball/mens-college-basketball", "NCAA Men's Basketball"),
    "nba": League("nba", "basketball", "basketball/nba", "NBA"),
    "nfl": League("nfl", "football", "football/nfl", "NFL"),
    "mlb": League("mlb", "baseball", "baseball/mlb", "MLB"),
    "nhl": League("nhl", "hockey", "hockey/nhl", "NHL"),
    # curated handful to start; extend by adding rows
}

def get_league(key: str) -> League | None: ...
```

### `backend/app/models/matchup.py` (new)

```python
@dataclass
class TeamRef:
    id: str
    name: str
    mascot: str
    color: str | None
    rank: int | None

@dataclass
class MatchupRequest:        # the raw ask from the API
    league_key: str
    team_a_id: str
    team_b_id: str

@dataclass
class MatchupContext:        # the resolved matchup the Scout phase produces
    league: League
    team_a: TeamRef
    team_b: TeamRef
    head_to_head_event: dict | None
    game_context: str
    stat_table: list[dict]          # rows: {stat, team_a, team_b}
    team_a_form: list[str]
    team_b_form: list[str]
```

### ESPN client (`clients/espn.py`)

The hardcoded basketball base URL is replaced by league-path injection:

- `fetch_team(league, team_id)`
- `fetch_schedule(league, team_id, season)`
- `fetch_teams(league)` — **new**; ESPN's `/teams` listing, used to populate the frontend selectors.

`fetch_scoreboard` is **removed**: its only consumer today is the deleted goal-parsing heuristic (`_resolve_matchup_event` scans `schedules + [scoreboard]`). The new deterministic head-to-head resolution reads only the two teams' schedules, so the scoreboard is no longer needed.

`ESPN_BASE_URL` is rebuilt per call as `https://site.api.espn.com/apis/site/v2/sports/{league.path}`.

### `config.py`

Keeps only infra config: `AWS_REGION`, `BEDROCK_MODEL_ID`, and the new defaults `DEFAULT_LEAGUE = "mens-college-basketball"`, `DEFAULT_TEAM_A = "356"` (Illinois), `DEFAULT_TEAM_B = "41"` (UConn). The standalone `ILLINOIS_TEAM_ID` / `UCONN_TEAM_ID` / `ESPN_BASE_URL` constants move out / are absorbed. `DEFAULT_GOAL` is **deleted** (the `?goal=` param is gone), along with its now-dangling import in `routes.py`.

---

## Section 2 — Pipeline restructuring (Scout phase)

`pipeline.run()` signature changes from `run(goal, emit)` to `run(request: MatchupRequest, emit)`.

### Deleted (≈150 lines of heuristics)

`_resolve_matchup_event`, `_event_match_score`, `_event_labels`, `_candidate_seasons`, `_extract_goal_years`, `ROUND_KEYWORDS`, and all Illinois/UConn ID branching. We now *know* both teams, so none of the goal-parsing inference is needed.

### New Scout flow (produces a `MatchupContext`)

1. `fetch_team(league, team_a_id)` and `fetch_team(league, team_b_id)`.
2. Fetch each team's schedule for the current season.
3. **Head-to-head resolution** (deterministic): scan team A's schedule for the event whose competitors include team B.
   - Found → drive `game_context`, ranks, and home/away from that event.
   - Not found (two teams not scheduled to meet — a valid open-domain case) → `head_to_head_event = None`; `game_context = "{league.label} Matchup"`; ranks fall back to each team's standalone curated/AP rank via the existing `_extract_ap_rank`, now called for **both** teams.
4. Build the symmetric `stat_table` via `_build_stat_comparison_table` (rows keyed `team_a`/`team_b`).
5. Extract `team_a_form` / `team_b_form` via the existing `_extract_recent_form`.
6. Scout LLM summary prompt generalized to "a {sport} matchup between {team_a} and {team_b}."

### Kept (already team-agnostic)

`_extract_recent_form`, `_extract_stat_map`, `_competitor_for_team`, `_competitors_from_event`, `_slim_team`, `_coerce_rank`, `_rank_from_event`, `_extract_ap_rank`, `_extract_competitor`, `_derive_game_context`, `_season_from_date` — they already take a `team_id` (or no team at all); they only lose Illinois defaults. (`_season_from_date` is retained to compute the current season for the schedule fetches, even though its old caller `_candidate_seasons` is deleted.)

### Rewritten / absorbed into `MatchupContext` construction

These are Illinois/UConn-coupled today and cannot survive the symmetric rewrite unchanged:

- `_build_team_header` → **absorbed**. The team header is now assembled from the two `TeamRef`s in `MatchupContext` (built symmetrically for team_a and team_b) rather than from an Illinois-anchored helper.
- `_team_display_fields` → **generalized** into a small `_team_ref(team_payload, event)` helper that extracts `(name, mascot, color, rank)` for *any* team; called once per side to build each `TeamRef`.
- `_opponent_competitor`, `_opponent_team_id` → **deleted**. There is no "opponent" concept; head-to-head resolution scans team A's schedule for team B's id directly, and ranks/competitors are read per-team via the kept `_competitor_for_team`.

### Analyst phase

Nearly unchanged — it only consumes text summaries. Team names are swapped into its prompt.

---

## Section 3 — Event contract rename + narrator

The SSE event shape is the backend↔frontend contract. Every `illinois_*` / `opponent_*` field becomes `team_a_*` / `team_b_*`.

### Event schema changes (`models/events.py` + frontend `types.ts`)

| Event | Today | Open-domain |
|---|---|---|
| `team_header` | `illinois_rank/name/mascot/color`, `opponent_*` | `team_a_rank/name/mascot/color`, `team_b_*`, `game_context` |
| `stat_comparison` | `illinois_value`, `opponent_value`, `illinois_pct` | `team_a_value`, `team_b_value`, `team_a_pct` |
| `win_probability` | `probability` (Illinois) | `team_a_probability` (P(team_a wins); UI derives team_b = 100 − team_a) |
| `key_factor` | `favors: "illinois"\|"opponent"` | `favors: "team_a"\|"team_b"` |
| `report_card` | grades Illinois only | adds `team: "team_a"\|"team_b"` so both teams are graded |
| `recent_form` | `team` (name), `results` | unchanged (already generic) |

`insight_card`, `matchup_preview`, `prediction`, `agent_thought`, `tool_call`, `tool_result`, `done` keep their shapes; only their content stops being Illinois-specific.

### Dead `chart` event removed

The `chart` event, `narrator.generate_charts`, and the frontend `charts` plumbing are emitted nowhere today. They are deleted as part of this rename to avoid confusion.

### Narrator inputs (the Section 2 ↔ Section 3 seam)

To keep the narrator decoupled from the domain model, the pipeline does **not** pass the whole `MatchupContext` into `run_narrator`. Instead it derives the same plain-data arguments the narrator takes today, renamed: `run_narrator(scout_summary, analyst_summary, emit, team_header: dict, stat_table: list, team_a_name: str, team_b_name: str)`. The `team_header` dict and `stat_table` are projected from `MatchupContext` in the pipeline; `team_a_name`/`team_b_name` are threaded in so prompts can name the teams. The narrator's interface stays plain dicts/lists, so it remains independently testable without constructing a `MatchupContext`.

### Narrator (`narrator.py`)

Structure is unchanged — 7 parallel generators + a dependent `prediction`. Changes:
- Every prompt swaps "Illinois"/"the Illini" for the two real team names (`team_a_name`/`team_b_name`).
- All anti-hallucination scaffolding stays verbatim (FACTUAL STATS block, placeholder filtering, pct clamping, dedup) — it is orthogonal to team identity and is the project's strongest asset.
- `generate_report_cards` grades both teams (each card tagged `team_a`/`team_b`).
- `generate_win_probability` returns a single P(team_a) float. The `win_probability` event keeps its current arity — exactly one field, renamed `probability → team_a_probability`. The backend does **not** emit a team_b value; the frontend `WinProbability` component derives team_b's share as `100 − team_a_probability` (it already renders both sides).
- `_normalize_stat_comparison_items` and `_merge_team_header` get the field renames.

---

## Section 4 — API surface & frontend

### API (`routes.py`)

- `GET /analyze` — params change from `?goal=` to `?league=<key>&team_a=<id>&team_b=<id>`. Validates league against the registry and that the two team IDs are present and **distinct**. Invalid league / missing / equal IDs → `agent_thought` error + `done` (no 500). Param-less call resolves to the Illini default.
- `GET /leagues` — **new**; returns `[{key, label, sport}]` for the league selector.
- `GET /teams?league=<key>` — **new**; returns `[{id, name}]` from `fetch_teams(league)` for the team selectors.
- `GET /health` — unchanged.

### Frontend

The single free-text box in `AnalysisPage.tsx` becomes three dependent selectors:

1. **League** dropdown (from `/leagues`), default **NCAA Men's Basketball**.
2. **Team A** and **Team B** dropdowns (from `/teams?league=`), Team A default **Illinois**, Team B default **UConn**.
3. **Mutual exclusion:** a team chosen in one selector is filtered out of the other (symmetric, regardless of pick order).
4. **League change resets both team selections** (team IDs are not valid across leagues).

`useAgentStream.start` takes `{league, teamA, teamB}` and builds the `?league&team_a&team_b` query. `state.ts` / `types.ts` get the `team_a`/`team_b` renames; `normalizeTeamHeader` defaults become neutral (`"Team A"` / `""`).

### Team colors (`teamColors.ts`)

The static Big Ten color map is dropped as the primary path. Colors come from ESPN's per-team hex (already plumbed via `*_color`), with a single neutral default fallback. Only a tiny generic palette remains as last resort.

### Components

`TeamHeader`, `WinProbability`, `StatComparisonChart`, `GroupedBarChart`, `KeyFactors`, `ReportCardGrid`, `Prediction`, `RecentForm` get mechanical `illinois`→`teamA` / `opponent`→`teamB` renames. `WinProbability` renders both sides from `team_a_probability`. `ReportCardGrid` groups cards by `team`.

### Branding

Frontend header "Illini Intel / Fighting Illini Basketball BI" → generic ("Matchup Intel"); orange theme becomes a neutral accent. Repo, package, and docs names are unchanged.

---

## Section 5 — Error handling & testing

### Error handling (keeps current philosophy — degrade gracefully, always emit `done`)

- Unknown league, missing or equal team IDs → `agent_thought` error + `done`.
- ESPN fetch failure for a team → Scout error path; analyst/narrator skipped; `done`.
- **No head-to-head game is not an error** — expected open-domain case (neutral `game_context`, standalone ranks).
- Bedrock throttling retry/backoff unchanged.

### Testing

- `leagues.py`: every entry has a valid sport/path.
- Scout: head-to-head **found** and **no-game fallback** (the main new branch).
- Narrator: existing JSON/stats/prediction tests get `team_a`/`team_b` renames; add a test that report cards can carry both teams (a `team_a` card and a `team_b` card). The `win_probability` event itself is asserted to carry the single `team_a_probability` field; the `100 − team_a` derivation is a **frontend** `WinProbability` unit test, not a backend assertion.
- ESPN client: `fetch_teams` + league-path injection (mock httpx).
- Frontend: `state.test.ts` / `statComparison.test.ts` / `predictionText.test.ts` updated for renamed fields; `normalizeTeamHeader` neutral defaults tested.
- Fixtures: keep an Illinois-vs-opponent fixture (regression guard) **and** add a non-college fixture (e.g. an NBA pair) to prove cross-league parameterization works.

---

## Out of scope (YAGNI)

- Non-ESPN data sources / provider abstraction.
- Renaming the repo, the `illini_intel_backend` package, or `docs/`.
- Persistence, scheduling, alerting, or any "continuous monitoring" — the tool stays request-driven and stateless.
- Reviving the removed `chart` event.

**Acknowledged drift:** `CLAUDE.md` and `README.md` describe "Fighting Illini" framing and the old event-field names. They are not rewritten here (doc churn, YAGNI), so they will be stale after this change. If desired, refreshing the `## Event contract` section of `CLAUDE.md` is a cheap follow-up — but it is not a blocker for implementation.
