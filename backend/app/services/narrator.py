from __future__ import annotations

import json
from typing import Any, Callable

from app.clients.bedrock import converse_text
from app.models import events

Emitter = Callable[[dict[str, Any]], None]


def _extract_json_object(raw: str) -> str:
    text = raw.strip()
    start = text.find("{")
    if start == -1:
        return text
    end = text.rfind("}")
    if end == -1 or end < start:
        return text[start:]
    return text[start : end + 1]


def _extract_json_array(raw: str) -> str:
    text = raw.strip()
    start = text.find("[")
    if start == -1:
        return text
    end = text.rfind("]")
    if end == -1 or end < start:
        return text[start:]
    return text[start : end + 1]


def _load_json_object(raw: str, fallback: dict[str, Any]) -> dict[str, Any]:
    try:
        data = json.loads(_extract_json_object(raw))
        return data if isinstance(data, dict) else fallback
    except json.JSONDecodeError:
        return fallback


def _load_json_array(raw: str) -> list[dict[str, Any]]:
    try:
        data = json.loads(_extract_json_array(raw))
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def generate_insight_card(context: str) -> dict[str, Any]:
    prompt = (
        f"{context}\n\n"
        "Extract 4-6 key Illinois basketball insights from the context. "
        "Respond with ONLY a JSON object, no other text:\n"
        '{"title": "<short title>", "data": {"key1": "value1", "key2": "value2"}}'
    )
    raw = converse_text(prompt, max_tokens=768)
    return _load_json_object(
        raw,
        {
            "title": "Illinois Basketball Insights",
            "data": {"summary": raw.strip() or "No structured insights returned."},
        },
    )


def generate_team_header(context: str) -> dict[str, Any]:
    prompt = (
        f"{context}\n\n"
        "Extract team matchup info. Respond with ONLY a JSON object, no other text:\n"
        '{"illinois_rank": <number or null>, "opponent_name": "<name>", '
        '"opponent_rank": <number or null>, "game_context": "<e.g. Regular Season, Final Four>"}'
    )
    raw = converse_text(prompt, max_tokens=384)
    return _load_json_object(
        raw,
        {
            "illinois_rank": None,
            "opponent_name": "Opponent",
            "opponent_rank": None,
            "game_context": "Illinois Basketball",
        },
    )


def generate_win_probability(context: str) -> float:
    prompt = (
        f"{context}\n\n"
        "Estimate Illinois win probability as a percentage from 0 to 100. "
        'Respond with ONLY a JSON object, no other text: {"probability": 61.0}'
    )
    raw = converse_text(prompt, max_tokens=256)
    data = _load_json_object(raw, {"probability": 50.0})
    try:
        value = float(data.get("probability", 50.0))
    except (TypeError, ValueError):
        value = 50.0
    return max(0.0, min(100.0, value))


def generate_stat_comparisons(context: str) -> list[dict[str, Any]]:
    prompt = (
        f"{context}\n\n"
        "Extract 4 key stat comparisons between Illinois and the opponent. "
        "illinois_pct is Illinois's share in [0.0, 1.0], where values over 0.5 mean Illinois leads. "
        "Respond with ONLY a JSON array, no other text."
    )
    return _load_json_array(converse_text(prompt, max_tokens=1024))


def generate_report_cards(context: str) -> list[dict[str, Any]]:
    prompt = (
        f"{context}\n\n"
        "Grade Illinois across 4 dimensions like Offense, Defense, Shooting, Rebounding. "
        "Grades must be one of A+, A, A-, B+, B, B-, C+, C. "
        "Respond with ONLY a JSON array, no other text."
    )
    return _load_json_array(converse_text(prompt, max_tokens=1024))


def generate_matchup_preview(context: str) -> str:
    prompt = (
        f"{context}\n\n"
        "Write a concise 2-3 sentence matchup preview for the Illinois game. "
        "Be specific about strengths, weaknesses, and key players. Plain text only."
    )
    return converse_text(prompt, max_tokens=512)


def generate_prediction(context: str) -> str:
    prompt = (
        f"{context}\n\n"
        "Based on the data, give a game prediction for Illinois including win probability, "
        "predicted score, and 1-2 sentence reasoning. Plain text only."
    )
    return converse_text(prompt, max_tokens=512)


def _merge_team_header(
    generated: dict[str, Any],
    team_header: dict[str, Any] | None,
) -> dict[str, Any]:
    if not team_header:
        return generated

    merged = dict(generated)
    for key in ("illinois_rank", "opponent_rank"):
        if team_header.get(key) is not None:
            merged[key] = team_header[key]

    if team_header.get("opponent_name"):
        merged["opponent_name"] = team_header["opponent_name"]

    if team_header.get("game_context"):
        merged["game_context"] = team_header["game_context"]

    return merged


def run_narrator(
    goal: str,
    scout_summary: str,
    analyst_summary: str,
    emit: Emitter,
    team_header: dict[str, Any] | None = None,
) -> None:
    emit(events.agent_thought("narrator", f"Generating BI report for: {goal}"))
    context = (
        f"Goal: {goal}\n\n"
        f"Scout data:\n{scout_summary}\n\n"
        f"Analyst findings:\n{analyst_summary}"
    )

    insight = generate_insight_card(context)
    emit(events.insight_card(insight.get("title", "Illinois Basketball Insights"), insight.get("data", {})))

    header = _merge_team_header(generate_team_header(context), team_header)
    emit(
        events.team_header(
            header.get("illinois_rank"),
            str(header.get("opponent_name", "Opponent")),
            header.get("opponent_rank"),
            str(header.get("game_context", "Illinois Basketball")),
        )
    )

    emit(events.win_probability(generate_win_probability(context)))

    for item in generate_stat_comparisons(context):
        try:
            pct = float(item.get("illinois_pct", 0.5))
        except (TypeError, ValueError):
            pct = 0.5
        emit(
            events.stat_comparison(
                str(item.get("label", "Stat")),
                str(item.get("illinois_value", "-")),
                str(item.get("opponent_value", "-")),
                max(0.0, min(1.0, pct)),
            )
        )

    for item in generate_report_cards(context):
        emit(
            events.report_card(
                str(item.get("dimension", "Dimension")),
                str(item.get("grade", "B")),
                str(item.get("stat", "")),
                str(item.get("explanation", "")),
            )
        )

    emit(events.matchup_preview(generate_matchup_preview(context)))
    emit(events.prediction(generate_prediction(context)))
