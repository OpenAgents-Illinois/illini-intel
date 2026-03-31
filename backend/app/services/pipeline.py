from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from app.clients.bedrock import converse_text
from app.clients.espn import fetch_schedule, fetch_scoreboard, fetch_team
from app.core.config import ILLINOIS_TEAM_ID, UCONN_TEAM_ID
from app.models import events
from app.services.narrator import run_narrator

Emitter = Callable[[dict[str, Any]], None]


def _extract_competitor(team_payload: dict[str, Any], team_id: str) -> dict[str, Any]:
    for event in team_payload.get("nextEvent", []):
        for competition in event.get("competitions", []):
            for competitor in competition.get("competitors", []):
                if str(competitor.get("team", {}).get("id")) == str(team_id):
                    return competitor
    return {}


def _extract_ap_rank(team_payload: dict[str, Any], team_id: str) -> int | None:
    competitor = _extract_competitor(team_payload, team_id)
    curated_rank = competitor.get("curatedRank", {}).get("current")
    if isinstance(curated_rank, int):
        return curated_rank

    top_level_rank = team_payload.get("rank")
    if isinstance(top_level_rank, int):
        return top_level_rank

    return None


def _build_team_header(illinois: dict[str, Any], opponent: dict[str, Any]) -> dict[str, Any]:
    return {
        "illinois_rank": _extract_ap_rank(illinois, ILLINOIS_TEAM_ID),
        "opponent_name": opponent.get("team", {}).get("displayName", "Opponent"),
        "opponent_rank": _extract_ap_rank(opponent, UCONN_TEAM_ID),
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

        emit(events.tool_call("scout", "fetch_team", {"team_id": UCONN_TEAM_ID}))
        opponent = fetch_team(UCONN_TEAM_ID)
        emit(
            events.tool_result(
                "scout",
                "fetch_team",
                {"team": opponent.get("team", {}).get("displayName", "UConn")},
            )
        )

        emit(events.tool_call("scout", "fetch_schedule", {"team_id": ILLINOIS_TEAM_ID}))
        schedule = fetch_schedule(ILLINOIS_TEAM_ID)
        emit(
            events.tool_result(
                "scout",
                "fetch_schedule",
                {"games": len(schedule.get("events", []))},
            )
        )

        emit(events.tool_call("scout", "fetch_scoreboard", {}))
        scoreboard = fetch_scoreboard()
        emit(
            events.tool_result(
                "scout",
                "fetch_scoreboard",
                {"games": len(scoreboard.get("events", []))},
            )
        )

        raw_context = {
            "illinois": illinois.get("team", {}),
            "opponent": opponent.get("team", {}),
            "schedule_event_count": len(schedule.get("events", [])),
            "scoreboard_event_count": len(scoreboard.get("events", [])),
        }
        team_header = _build_team_header(illinois, opponent)
        prompt = (
            f"Goal: {goal}\n\n"
            "You are the Scout agent for Illini Intel. Review this ESPN-derived context and write "
            "a concise scouting summary for downstream analysis. Focus on matchup context, team identity, "
            "and what Illinois needs to control. Plain text only.\n\n"
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
            run_narrator(goal, scout_summary, analyst_summary, emit, team_header=team_header)
        except Exception as error:
            emit(events.agent_thought("narrator", f"Narrator error: {error!r}"))

    emit(events.done())
