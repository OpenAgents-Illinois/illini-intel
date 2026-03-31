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
    illinois_rank: int | None,
    illinois_name: str,
    illinois_mascot: str,
    opponent_name: str,
    opponent_mascot: str,
    opponent_rank: int | None,
    game_context: str,
) -> dict[str, Any]:
    return {
        "type": "team_header",
        "illinois_rank": illinois_rank,
        "illinois_name": illinois_name,
        "illinois_mascot": illinois_mascot,
        "opponent_name": opponent_name,
        "opponent_mascot": opponent_mascot,
        "opponent_rank": opponent_rank,
        "game_context": game_context,
    }


def stat_comparison(
    label: str,
    illinois_value: str,
    opponent_value: str,
    illinois_pct: float,
) -> dict[str, Any]:
    return {
        "type": "stat_comparison",
        "label": label,
        "illinois_value": illinois_value,
        "opponent_value": opponent_value,
        "illinois_pct": illinois_pct,
    }


def report_card(
    dimension: str,
    grade: str,
    stat: str,
    explanation: str,
) -> dict[str, Any]:
    return {
        "type": "report_card",
        "dimension": dimension,
        "grade": grade,
        "stat": stat,
        "explanation": explanation,
    }


def win_probability(probability: float) -> dict[str, Any]:
    return {"type": "win_probability", "probability": probability}


def done() -> dict[str, str]:
    return {"type": "done"}
