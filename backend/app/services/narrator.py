from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
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


def _is_placeholder_text(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    normalized = value.strip().lower()
    return normalized in {"", "-", "n/a", "na", "unknown", "none", "stat", "metric", "value"}


def _normalize_stat_comparison_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized_items: list[dict[str, Any]] = []
    seen_labels: set[str] = set()

    for item in items:
        label = str(item.get("label", "")).strip()
        illinois_value = str(item.get("illinois_value", "")).strip()
        opponent_value = str(item.get("opponent_value", "")).strip()

        if _is_placeholder_text(label):
            continue
        if _is_placeholder_text(illinois_value) and _is_placeholder_text(opponent_value):
            continue

        try:
            pct = float(item.get("illinois_pct", 0.5))
        except (TypeError, ValueError):
            continue

        if not 0.0 <= pct <= 1.0:
            continue

        dedupe_key = label.lower()
        if dedupe_key in seen_labels:
            continue
        seen_labels.add(dedupe_key)

        normalized_items.append(
            {
                "label": label,
                "illinois_value": illinois_value or "-",
                "opponent_value": opponent_value or "-",
                "illinois_pct": pct,
            }
        )

    return normalized_items[:4]


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
        '{"illinois_rank": <number or null>, "illinois_name": "<school>", "illinois_mascot": "<mascot>", '
        '"opponent_name": "<school>", "opponent_mascot": "<mascot>", '
        '"opponent_rank": <number or null>, "game_context": "<e.g. Regular Season, Final Four>"}'
    )
    raw = converse_text(prompt, max_tokens=384)
    return _load_json_object(
        raw,
        {
            "illinois_rank": None,
            "illinois_name": "Illinois",
            "illinois_mascot": "Fighting Illini",
            "opponent_name": "Opponent",
            "opponent_mascot": "",
            "opponent_rank": None,
            "game_context": "Illinois Basketball",
        },
    )


def generate_win_probability(context: str) -> float:
    prompt = (
        f"{context}\n\n"
        "Based solely on the scout data and analyst findings above, estimate the Illinois win probability. "
        "Return a float between 0 and 100 reflecting a realistic, evidence-based assessment. "
        'Respond with ONLY a JSON object: {"probability": <float 0-100>}'
    )
    raw = converse_text(prompt, max_tokens=256)
    data = _load_json_object(raw, {"probability": 50.0})
    try:
        value = float(data.get("probability", 50.0))
    except (TypeError, ValueError):
        value = 50.0
    return max(0.0, min(100.0, value))


def generate_stat_comparisons(context: str, stat_comparison_table: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    if stat_comparison_table:
        table_json = json.dumps(stat_comparison_table)
        table_note = (
            f"AVAILABLE STATS (use ONLY these — do not invent values):\n{table_json}\n\n"
            "Each entry has 'stat', 'illinois', and 'opponent' fields from ESPN. "
            "illinois_pct must be computed from the two real values (illinois / (illinois + opponent)), clamped to [0.0, 1.0].\n\n"
        )
    else:
        table_note = ""
    prompt = (
        f"{context}\n\n"
        f"{table_note}"
        "Pick the 4 most meaningful stats for this matchup from the available stats above. "
        "Use ONLY real values from the table — never invent numbers. "
        "Omit any stat where either value is missing or non-numeric. "
        "Use the exact stat name as the label. "
        'Respond with ONLY a JSON array. Each element: "label" (string), "illinois_value" (string), "opponent_value" (string), "illinois_pct" (float 0.0-1.0).'
    )
    return _normalize_stat_comparison_items(
        _load_json_array(converse_text(prompt, max_tokens=1024))
    )


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
        "Write a thorough matchup preview for serious Illinois basketball fans. "
        "Use 3 short paragraphs with 2-3 sentences each and separate each paragraph with a blank line. "
        "Include specific player history, rotation context, recent form, "
        "shot profile, rebounding or turnover dynamics, and any advanced-stat style angles that are supported by the context. "
        "If the context mentions prior meetings, NCAA tournament history, or notable player development, include that too. "
        "Plain text only."
    )
    return converse_text(prompt, max_tokens=512)


def generate_charts(context: str, stat_comparison_table: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    if stat_comparison_table:
        table_json = json.dumps(stat_comparison_table)
        table_note = (
            f"AVAILABLE STATS (use ONLY these — do not invent values):\n{table_json}\n\n"
            "Each entry has 'stat', 'illinois', and 'opponent' fields with real ESPN values.\n\n"
        )
    else:
        table_note = ""
    prompt = (
        f"{context}\n\n"
        f"{table_note}"
        "Group the available stats above into 2-3 meaningful chart groups (e.g. Scoring, Rebounding, Shooting). "
        "Use ONLY stat names and values from the table above — never invent numbers. "
        "Each series item must use the exact 'illinois' and 'opponent' values from the table. "
        'Respond with ONLY a JSON array. Each element: {"title": "<chart title>", "series": [{"label": "<stat name>", "illinois": "<value from table>", "opponent": "<value from table>"}, ...]}'
    )
    raw = converse_text(prompt, max_tokens=1024)
    items = _load_json_array(raw)
    charts: list[dict[str, Any]] = []
    for item in items:
        title = str(item.get("title", "")).strip()
        series = item.get("series", [])
        if not title or not isinstance(series, list) or not series:
            continue
        valid_series = []
        for s in series:
            label = str(s.get("label", "")).strip()
            illinois = str(s.get("illinois", "")).strip()
            opponent = str(s.get("opponent", "")).strip()
            if label and illinois and opponent and not _is_placeholder_text(illinois) and not _is_placeholder_text(opponent):
                valid_series.append({"label": label, "illinois": illinois, "opponent": opponent})
        if valid_series:
            charts.append({"title": title, "series": valid_series})
    return charts[:3]


def generate_key_factors(context: str) -> list[dict[str, Any]]:
    prompt = (
        f"{context}\n\n"
        "Identify 3-4 key swing factors that will decide this game, drawn only from the context above. "
        "For each factor specify who it favors. "
        'Respond with ONLY a JSON array. Each element: {"label": "<specific factor name>", "detail": "<1 sentence explanation>", "favors": "illinois" or "opponent" or "neutral"}. '
        "Labels must be specific (e.g. 'Illinois 3PT Defense') — never generic like 'Key Factor'."
    )
    raw = converse_text(prompt, max_tokens=768)
    items = _load_json_array(raw)
    result: list[dict[str, Any]] = []
    for item in items:
        label = str(item.get("label", "")).strip()
        detail = str(item.get("detail", "")).strip()
        favors = str(item.get("favors", "neutral")).strip().lower()
        if not label or not detail:
            continue
        if favors not in {"illinois", "opponent", "neutral"}:
            favors = "neutral"
        result.append({"label": label, "detail": detail, "favors": favors})
    return result[:4]


def generate_prediction(context: str, win_probability: float) -> str:
    prompt = (
        f"{context}\n\n"
        f"Use this exact Illinois win probability in your response: {win_probability:.1f}%.\n"
        "Based on the data, give a game prediction for Illinois including the exact win probability above, "
        "a predicted score, and 2 short paragraphs of reasoning separated by a blank line. "
        "The first paragraph should state the prediction cleanly. "
        "The second paragraph should explain why using the matchup details. "
        "Do not invent a different probability. Plain text only."
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

    for key in ("illinois_name", "illinois_mascot", "opponent_name", "opponent_mascot"):
        if team_header.get(key):
            merged[key] = team_header[key]

    if team_header.get("game_context"):
        merged["game_context"] = team_header["game_context"]

    return merged


def run_narrator(
    goal: str,
    scout_summary: str,
    analyst_summary: str,
    emit: Emitter,
    team_header: dict[str, Any] | None = None,
    stat_comparison_table: list[dict[str, Any]] | None = None,
) -> None:
    emit(events.agent_thought("narrator", f"Generating BI report for: {goal}"))
    context = (
        f"Goal: {goal}\n\n"
        f"Scout data:\n{scout_summary}\n\n"
        f"Analyst findings:\n{analyst_summary}"
    )

    # Run all independent LLM calls in parallel; prediction waits for win_probability
    tasks = {
        "insight": lambda: generate_insight_card(context),
        "header": lambda: generate_team_header(context),
        "win_prob": lambda: generate_win_probability(context),
        "stat_comparisons": lambda: generate_stat_comparisons(context, stat_comparison_table),
        "report_cards": lambda: generate_report_cards(context),
        "charts": lambda: generate_charts(context, stat_comparison_table),
        "key_factors": lambda: generate_key_factors(context),
        "matchup_preview": lambda: generate_matchup_preview(context),
    }

    results: dict[str, Any] = {}
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(fn): name for name, fn in tasks.items()}
        for future in as_completed(futures):
            name = futures[future]
            try:
                results[name] = future.result()
            except Exception as exc:
                emit(events.agent_thought("narrator", f"Narrator sub-task '{name}' error: {exc!r}"))
                results[name] = None

    # Emit in logical UI order
    insight = results.get("insight") or {}
    emit(events.insight_card(insight.get("title", "Illinois Basketball Insights"), insight.get("data", {})))

    header = _merge_team_header(results.get("header") or {}, team_header)
    emit(
        events.team_header(
            header.get("illinois_rank"),
            str(header.get("illinois_name", "Illinois")),
            str(header.get("illinois_mascot", "Fighting Illini")),
            str(header.get("opponent_name", "Opponent")),
            str(header.get("opponent_mascot", "")),
            header.get("opponent_rank"),
            str(header.get("game_context", "Illinois Basketball")),
        )
    )

    win_probability: float = results.get("win_prob") or 50.0
    emit(events.win_probability(win_probability))

    for item in results.get("stat_comparisons") or []:
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

    for item in results.get("report_cards") or []:
        emit(
            events.report_card(
                str(item.get("dimension", "Dimension")),
                str(item.get("grade", "B")),
                str(item.get("stat", "")),
                str(item.get("explanation", "")),
            )
        )

    for ch in results.get("charts") or []:
        emit(events.chart("grouped_bars", ch["title"], ch["series"]))

    for factor in results.get("key_factors") or []:
        emit(events.key_factor(factor["label"], factor["detail"], factor["favors"]))

    emit(events.matchup_preview(results.get("matchup_preview") or ""))

    # prediction depends on win_probability — run after parallel batch
    try:
        prediction_text = generate_prediction(context, win_probability)
    except Exception as exc:
        emit(events.agent_thought("narrator", f"Prediction error: {exc!r}"))
        prediction_text = ""
    emit(events.prediction(prediction_text))
