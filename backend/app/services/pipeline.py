from __future__ import annotations

import json
import re
from collections.abc import Callable
from datetime import datetime
from typing import Any

from app.clients.bedrock import converse_text
from app.clients.espn import fetch_schedule, fetch_scoreboard, fetch_team
from app.core.config import ILLINOIS_TEAM_ID, UCONN_TEAM_ID
from app.models import events
from app.services.narrator import run_narrator

Emitter = Callable[[dict[str, Any]], None]

ROUND_KEYWORDS = (
    "final four",
    "elite 8",
    "elite eight",
    "sweet 16",
    "sweet sixteen",
    "round of 32",
    "round of 64",
    "big ten tournament",
    "ncaa tournament",
    "postseason",
    "regular season",
)


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


def _extract_goal_years(goal: str) -> list[int]:
    years: list[int] = []
    for first, second in re.findall(r"\b(20\d{2})[-/](\d{2,4})\b", goal):
        if len(second) == 2:
            years.append(int(first[:2] + second))
        else:
            years.append(int(second))
    years.extend(int(year) for year in re.findall(r"\b(20\d{2})\b", goal))
    return list(dict.fromkeys(years))


def _candidate_seasons(goal: str, now: datetime | None = None) -> list[int]:
    explicit = _extract_goal_years(goal)
    if explicit:
        return explicit

    current = _season_from_date(now)
    lowered = goal.lower()
    if any(keyword in lowered for keyword in ROUND_KEYWORDS):
        return [current - offset for offset in range(0, 8)]

    return [current]


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


def _opponent_competitor(event: dict[str, Any] | None) -> dict[str, Any]:
    if not event:
        return {}
    for competitor in _competitors_from_event(event):
        if str(competitor.get("team", {}).get("id")) != ILLINOIS_TEAM_ID:
            return competitor
    return {}


def _opponent_team_id(event: dict[str, Any] | None) -> str | None:
    competitor = _opponent_competitor(event)
    team_id = competitor.get("team", {}).get("id")
    return str(team_id) if team_id is not None else None


def _event_labels(event: dict[str, Any]) -> str:
    competition = (event.get("competitions") or [{}])[0]
    note = ((competition.get("notes") or [{}])[0]).get("headline", "")
    pieces = [
        event.get("name", ""),
        event.get("shortName", ""),
        note,
        competition.get("type", {}).get("text", ""),
        competition.get("type", {}).get("abbreviation", ""),
    ]
    competitors = _competitors_from_event(event)
    for competitor in competitors:
        team = competitor.get("team", {})
        pieces.extend(
            [
                team.get("displayName", ""),
                team.get("shortDisplayName", ""),
                team.get("location", ""),
                team.get("name", ""),
                team.get("nickname", ""),
            ]
        )
    return " ".join(piece for piece in pieces if piece).lower()


def _event_match_score(goal: str, event: dict[str, Any]) -> int:
    lowered = goal.lower()
    labels = _event_labels(event)
    score = 0

    if "vs " in lowered or "@" in lowered or "against" in lowered or "matchup" in lowered:
        competitors = _competitors_from_event(event)
        opponent_labels = []
        for competitor in competitors:
            team = competitor.get("team", {})
            if str(team.get("id")) == ILLINOIS_TEAM_ID:
                continue
            opponent_labels.extend(
                label.lower()
                for label in (
                    team.get("displayName"),
                    team.get("shortDisplayName"),
                    team.get("location"),
                    team.get("nickname"),
                    team.get("abbreviation"),
                )
                if label
            )
        if any(label in lowered for label in opponent_labels):
            score += 6

    for keyword in ROUND_KEYWORDS:
        if keyword in lowered and keyword in labels:
            score += 4

    for year in _extract_goal_years(goal):
        if str(year) in labels:
            score += 2

    if any(word in lowered for word in ("upcoming", "next", "tonight", "today")):
        status = event.get("status", {}).get("type", {}).get("name", "")
        if status in {"STATUS_SCHEDULED", "STATUS_IN_PROGRESS"}:
            score += 2

    return score


def _resolve_matchup_event(goal: str, schedules: list[dict[str, Any]]) -> dict[str, Any] | None:
    best_event: dict[str, Any] | None = None
    best_score = 0
    for schedule in schedules:
        for event in schedule.get("events", []):
            if not isinstance(event, dict):
                continue
            score = _event_match_score(goal, event)
            if score > best_score:
                best_score = score
                best_event = event
    return best_event


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


def _team_display_fields(team_payload: dict[str, Any], fallback_name: str, fallback_mascot: str) -> tuple[str, str]:
    team = team_payload.get("team", {})
    return (
        team.get("shortDisplayName", fallback_name),
        team.get("name", fallback_mascot),
    )


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


def _slim_team(team_payload: dict[str, Any]) -> dict[str, Any]:
    """Return only identity and statistics fields to keep context compact."""
    team = team_payload.get("team", {})
    return {
        "id": team.get("id"),
        "displayName": team.get("displayName"),
        "shortDisplayName": team.get("shortDisplayName"),
        "abbreviation": team.get("abbreviation"),
        "record": team.get("record"),
        "statistics": team.get("statistics"),
        "ranks": team.get("ranks"),
    }


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
    illinois_payload: dict[str, Any],
    opponent_payload: dict[str, Any],
) -> list[dict[str, Any]]:
    """Return a list of {stat, illinois, opponent} rows for stats present in both teams."""
    illinois_stats = _extract_stat_map(illinois_payload)
    opponent_stats = _extract_stat_map(opponent_payload)
    shared = sorted(set(illinois_stats) & set(opponent_stats))
    return [
        {"stat": k, "illinois": illinois_stats[k], "opponent": opponent_stats[k]}
        for k in shared
    ]


def _build_team_header(
    illinois: dict[str, Any],
    opponent: dict[str, Any],
    matchup_event: dict[str, Any] | None = None,
) -> dict[str, Any]:
    illinois_name, illinois_mascot = _team_display_fields(illinois, "Illinois", "Fighting Illini")
    opponent_name, opponent_mascot = _team_display_fields(opponent, "Opponent", "")

    if matchup_event:
        illinois_competitor = _competitor_for_team(matchup_event, ILLINOIS_TEAM_ID)
        opponent_competitor = _opponent_competitor(matchup_event)
        illinois_team = illinois_competitor.get("team", {})
        opponent_team = opponent_competitor.get("team", {})
        if illinois_team:
            illinois_name = illinois_team.get("shortDisplayName", illinois_team.get("location", illinois_name))
            illinois_mascot = illinois_team.get("name", illinois_team.get("nickname", illinois_mascot))
        if opponent_team:
            opponent_name = opponent_team.get("shortDisplayName", opponent_team.get("location", opponent_name))
            opponent_mascot = opponent_team.get("name", opponent_team.get("nickname", opponent_mascot))

    return {
        "illinois_rank": _rank_from_event(matchup_event, ILLINOIS_TEAM_ID)
        if matchup_event
        else _extract_ap_rank(illinois, ILLINOIS_TEAM_ID),
        "illinois_name": illinois_name,
        "illinois_mascot": illinois_mascot,
        "opponent_name": opponent_name,
        "opponent_mascot": opponent_mascot,
        "opponent_rank": _rank_from_event(matchup_event, _opponent_team_id(matchup_event) or UCONN_TEAM_ID)
        if matchup_event
        else _extract_ap_rank(opponent, UCONN_TEAM_ID),
        "game_context": _derive_game_context(matchup_event),
    }


def run(goal: str, emit: Emitter) -> None:
    emit(events.agent_thought("scout", f"Starting scout agent with goal: {goal}"))
    scout_summary = ""
    team_header: dict[str, Any] | None = None

    try:
        emit(events.tool_call("scout", "fetch_team", {"team_id": ILLINOIS_TEAM_ID}))
        illinois = fetch_team(ILLINOIS_TEAM_ID)
        emit(
            events.tool_result(
                "scout",
                "fetch_team",
                {"team": illinois.get("team", {}).get("displayName", "Illinois")},
            )
        )

        seasons = _candidate_seasons(goal)
        schedules: list[dict[str, Any]] = []
        for season in seasons:
            emit(events.tool_call("scout", "fetch_schedule", {"team_id": ILLINOIS_TEAM_ID, "season": season}))
            schedule = fetch_schedule(ILLINOIS_TEAM_ID, season=season)
            schedules.append(schedule)
            emit(
                events.tool_result(
                    "scout",
                    "fetch_schedule",
                    {"season": season, "games": len(schedule.get("events", []))},
                )
            )
        schedule = schedules[0] if schedules else {"events": []}

        emit(events.tool_call("scout", "fetch_scoreboard", {}))
        scoreboard = fetch_scoreboard()
        emit(
            events.tool_result(
                "scout",
                "fetch_scoreboard",
                {"games": len(scoreboard.get("events", []))},
            )
        )

        matchup_event = _resolve_matchup_event(goal, schedules + [scoreboard])
        opponent_id = _opponent_team_id(matchup_event) or UCONN_TEAM_ID
        emit(events.tool_call("scout", "fetch_team", {"team_id": opponent_id}))
        opponent = fetch_team(opponent_id)
        emit(
            events.tool_result(
                "scout",
                "fetch_team",
                {"team": opponent.get("team", {}).get("displayName", "Opponent")},
            )
        )

        emit(events.tool_call("scout", "fetch_schedule", {"team_id": opponent_id, "season": seasons[0]}))
        opponent_schedule = fetch_schedule(opponent_id, season=seasons[0])
        emit(
            events.tool_result(
                "scout",
                "fetch_schedule",
                {"team": "opponent", "season": seasons[0], "games": len(opponent_schedule.get("events", []))},
            )
        )

        team_header = _build_team_header(illinois, opponent, matchup_event)
        stat_comparison_table = _build_stat_comparison_table(illinois, opponent)

        illinois_form = _extract_recent_form(schedules[0], ILLINOIS_TEAM_ID)
        opponent_form = _extract_recent_form(opponent_schedule, opponent_id)
        emit(events.recent_form(team_header.get("illinois_name", "Illinois"), illinois_form))
        emit(events.recent_form(team_header.get("opponent_name", "Opponent"), opponent_form))

        raw_context = {
            "illinois": _slim_team(illinois),
            "opponent": _slim_team(opponent),
            "stat_comparison_table": stat_comparison_table,
            "team_header": team_header,
            "matchup_event": matchup_event,
        }
        illinois_name = team_header.get("illinois_name", "Illinois")
        opponent_name = team_header.get("opponent_name", "Opponent")
        prompt = (
            f"Goal: {goal}\n\n"
            "You are the Scout agent for Illini Intel. Review this ESPN-derived context and write "
            "a concise scouting summary for downstream analysis. "
            f"The stat_comparison_table contains side-by-side season averages for {illinois_name} and {opponent_name} — "
            "explicitly mention key stats (scoring, rebounds, turnovers, tempo, shooting) for BOTH teams by name. "
            "Focus on matchup context and what Illinois needs to control. Plain text only.\n\n"
            f"Context:\n{json.dumps(raw_context, default=str)[:12000]}"
        )
        scout_summary = converse_text(prompt, max_tokens=900)
    except Exception as error:
        scout_summary = "Scout error"
        emit(events.agent_thought("scout", f"Scout error: {error!r}"))

    emit(events.agent_thought("analyst", f"Starting analyst agent with goal: {goal}"))
    analyst_summary = ""
    if scout_summary == "Scout error":
        analyst_summary = "Analyst error"
        emit(events.agent_thought("analyst", "Analyst skipped because scout failed."))
    else:
        try:
            prompt = (
                f"Goal: {goal}\n\n"
                f"Scout summary:\n{scout_summary}\n\n"
                "You are the Illini Intel analyst. Produce a concise analysis covering matchup dynamics, "
                "risk factors, and 4-6 concrete takeaways. Plain text, no JSON."
            )
            analyst_summary = converse_text(prompt, max_tokens=900)
        except Exception as error:
            analyst_summary = "Analyst error"
            emit(events.agent_thought("analyst", f"Analyst error: {error!r}"))

    if scout_summary == "Scout error" or analyst_summary == "Analyst error":
        emit(events.agent_thought("narrator", "Skipping narrator because upstream agents failed."))
    else:
        try:
            run_narrator(goal, scout_summary, analyst_summary, emit, team_header=team_header, stat_comparison_table=stat_comparison_table)
        except Exception as error:
            emit(events.agent_thought("narrator", f"Narrator error: {error!r}"))

    emit(events.done())
