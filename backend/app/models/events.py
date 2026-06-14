from __future__ import annotations

from typing import Any


def agent_thought(agent: str, content: str) -> dict[str, Any]:
    return {"type": "agent_thought", "agent": agent, "content": content}


def tool_call(agent: str, tool: str, args: dict[str, Any]) -> dict[str, Any]:
    return {"type": "tool_call", "agent": agent, "tool": tool, "args": args}


def tool_result(agent: str, tool: str, result: dict[str, Any]) -> dict[str, Any]:
    return {"type": "tool_result", "agent": agent, "tool": tool, "result": result}


def insight_card(title: str, data: dict[str, Any]) -> dict[str, Any]:
    return {"type": "insight_card", "title": title, "data": data}


def matchup_preview(content: str) -> dict[str, Any]:
    return {"type": "matchup_preview", "content": content}


def prediction(content: str) -> dict[str, Any]:
    return {"type": "prediction", "content": content}


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


def recent_form(team: str, results: list[str]) -> dict[str, Any]:
    return {"type": "recent_form", "team": team, "results": results}


def key_factor(label: str, detail: str, favors: str) -> dict[str, Any]:
    return {"type": "key_factor", "label": label, "detail": detail, "favors": favors}


def done() -> dict[str, str]:
    return {"type": "done"}
