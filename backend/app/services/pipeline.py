from __future__ import annotations

import json
from collections.abc import Callable
from datetime import datetime
from typing import Any

from app.clients.bedrock import converse_text
from app.clients.espn import fetch_schedule, fetch_team
from app.core.leagues import League, get_league
from app.models import events
from app.models.matchup import MatchupContext, MatchupRequest, TeamRef
from app.services.narrator import run_narrator

Emitter = Callable[[dict[str, Any]], None]


def _coerce_rank(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        digits = "".join(ch for ch in value if ch.isdigit())
        if digits:
            return int(digits)
    return None


def _extract_competitor(team_payload: dict[str, Any], team_id: str) -> dict[str, Any]:
    for event in team_payload.get("nextEvent", []):
        for competition in event.get("competitions", []):
            for competitor in competition.get("competitors", []):
                if str(competitor.get("team", {}).get("id")) == str(team_id):
                    return competitor
    return {}


def _extract_ap_rank(team_payload: dict[str, Any], team_id: str) -> int | None:
    competitor = _extract_competitor(team_payload, team_id)
    candidates = (
        competitor.get("curatedRank", {}).get("current"),
        competitor.get("rank"),
        team_payload.get("rank"),
        team_payload.get("team", {}).get("rank"),
        team_payload.get("team", {}).get("curatedRank", {}).get("current"),
        team_payload.get("ranks", [{}])[0].get("current") if team_payload.get("ranks") else None,
    )
    for candidate in candidates:
        rank = _coerce_rank(candidate)
        if rank is not None:
            return rank

    return None


def _season_from_date(now: datetime | None = None) -> int:
    current = now or datetime.now()
    return current.year + 1 if current.month >= 7 else current.year


def _competitors_from_event(event: dict[str, Any]) -> list[dict[str, Any]]:
    for competition in event.get("competitions", []):
        competitors = competition.get("competitors", [])
        if competitors:
            return competitors
    return []


def _competitor_for_team(event: dict[str, Any], team_id: str) -> dict[str, Any]:
    for competitor in _competitors_from_event(event):
        if str(competitor.get("team", {}).get("id")) == str(team_id):
            return competitor
    return {}


def _derive_game_context(event: dict[str, Any] | None) -> str | None:
    if not event:
        return None

    competition = (event.get("competitions") or [{}])[0]
    note = ((competition.get("notes") or [{}])[0]).get("headline")
    if isinstance(note, str) and note.strip():
        parts = [part.strip() for part in note.split(" - ") if part.strip()]
        return parts[-1] if parts else note.strip()

    season_type = competition.get("type", {}).get("text")
    if isinstance(season_type, str) and season_type.strip():
        return season_type.strip()

    return None


def _rank_from_event(event: dict[str, Any] | None, team_id: str) -> int | None:
    if not event:
        return None
    competitor = _competitor_for_team(event, team_id)
    candidates = (
        competitor.get("curatedRank", {}).get("current"),
        competitor.get("rank"),
        competitor.get("team", {}).get("rank"),
    )
    for candidate in candidates:
        rank = _coerce_rank(candidate)
        if rank is not None:
            return rank
    return None


def _extract_recent_form(schedule: dict[str, Any], team_id: str, n: int = 5) -> list[str]:
    """Return the last n W/L results for team_id from a completed-game schedule."""
    results: list[str] = []
    for event in reversed(schedule.get("events", [])):
        if not isinstance(event, dict):
            continue

        # ESPN puts status on the event or on competitions[0]
        event_status = event.get("status", {}).get("type", {}).get("name", "")
        competition = (event.get("competitions") or [{}])[0]
        comp_status = (
            competition.get("status", {}).get("type", {}).get("name", "")
            if isinstance(competition, dict)
            else ""
        )
        status = event_status or comp_status
        if "FINAL" not in status.upper():
            continue

        competitor = _competitor_for_team(event, team_id)
        if not competitor:
            continue

        winner = competitor.get("winner")
        if winner is True or winner == "true":
            results.append("W")
        elif winner is False or winner == "false":
            results.append("L")
        else:
            # Fall back to score comparison
            score = competitor.get("score")
            if score is not None:
                for c in _competitors_from_event(event):
                    if str(c.get("team", {}).get("id")) != str(team_id):
                        opp_score = c.get("score")
                        if opp_score is not None:
                            try:
                                results.append("W" if float(score) > float(opp_score) else "L")
                            except (TypeError, ValueError):
                                pass
                        break

        if len(results) >= n:
            break
    return results


def _extract_stat_map(team_payload: dict[str, Any]) -> dict[str, Any]:
    """Extract a flat name→value map from ESPN statistics array."""
    team = team_payload.get("team", {})
    stats: dict[str, Any] = {}
    for entry in team.get("statistics", []) or []:
        name = entry.get("displayName") or entry.get("name")
        value = entry.get("displayValue") or entry.get("value")
        if name and value is not None:
            stats[name] = value
    return stats


def _build_stat_comparison_table(
    team_a_payload: dict[str, Any],
    team_b_payload: dict[str, Any],
) -> list[dict[str, Any]]:
    """Return a list of {stat, team_a, team_b} rows for stats present in both teams."""
    team_a_stats = _extract_stat_map(team_a_payload)
    team_b_stats = _extract_stat_map(team_b_payload)
    shared = sorted(set(team_a_stats) & set(team_b_stats))
    return [
        {"stat": k, "team_a": team_a_stats[k], "team_b": team_b_stats[k]}
        for k in shared
    ]


def _slim_team_by_name(team_ref: TeamRef) -> dict[str, Any]:
    return {"name": team_ref.name, "mascot": team_ref.mascot, "rank": team_ref.rank}


def _team_ref(league: League, team_payload: dict[str, Any], team_id: str, event: dict[str, Any] | None) -> TeamRef:
    team = team_payload.get("team", {})
    name = team.get("shortDisplayName") or team.get("displayName") or team.get("location") or "Team"
    mascot = team.get("name") or team.get("nickname") or ""
    color = team.get("color")
    rank = _rank_from_event(event, team_id) if event else _extract_ap_rank(team_payload, team_id)
    return TeamRef(id=str(team_id), name=name, mascot=mascot, color=color, rank=rank)


def _find_head_to_head(schedule: dict[str, Any], opponent_id: str) -> dict[str, Any] | None:
    for event in schedule.get("events", []):
        if not isinstance(event, dict):
            continue
        for competitor in _competitors_from_event(event):
            if str(competitor.get("team", {}).get("id")) == str(opponent_id):
                return event
    return None


def _team_header_dict(ctx: MatchupContext) -> dict[str, Any]:
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


def _scout(league: League, request: MatchupRequest, emit: Emitter) -> MatchupContext:
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


def _scout_summary(ctx: MatchupContext) -> str:
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


def run(request: MatchupRequest, emit: Emitter) -> None:
    league = get_league(request.league_key)
    if league is None:
        emit(events.agent_thought("scout", f"Unknown league: {request.league_key!r}"))
        emit(events.done())
        return

    emit(events.agent_thought("scout", f"Scouting {league.label}: {request.team_a_id} vs {request.team_b_id}"))
    scout_summary = ""
    ctx: MatchupContext | None = None
    try:
        ctx = _scout(league, request, emit)
        scout_summary = _scout_summary(ctx)
    except Exception as error:
        scout_summary = "Scout error"
        emit(events.agent_thought("scout", f"Scout error: {error!r}"))

    emit(events.agent_thought("analyst", "Starting analyst agent"))
    analyst_summary = ""
    if scout_summary == "Scout error" or ctx is None:
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

    if scout_summary == "Scout error" or analyst_summary == "Analyst error" or ctx is None:
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
