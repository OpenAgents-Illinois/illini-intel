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
        team_a_value = str(item.get("team_a_value", "")).strip()
        team_b_value = str(item.get("team_b_value", "")).strip()

        if _is_placeholder_text(label):
            continue
        if _is_placeholder_text(team_a_value) or _is_placeholder_text(team_b_value):
            continue

        try:
            pct = float(item.get("team_a_pct", 0.5))
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
                "team_a_value": team_a_value or "-",
                "team_b_value": team_b_value or "-",
                "team_a_pct": pct,
            }
        )

    return normalized_items[:4]


def generate_insight_card(context: str) -> dict[str, Any]:
    prompt = (
        f"{context}\n\n"
        "Extract 4-6 key insights about this matchup from the context. "
        "Any numeric values (stats, records, ranks) must come from the FACTUAL ESPN STATS section above — do not invent numbers. "
        "Respond with ONLY a JSON object, no other text:\n"
        '{"title": "<short title>", "data": {"key1": "value1", "key2": "value2"}}'
    )
    raw = converse_text(prompt, max_tokens=768)
    return _load_json_object(
        raw,
        {
            "title": "Matchup Insights",
            "data": {"summary": raw.strip() or "No structured insights returned."},
        },
    )


def generate_team_header(context: str) -> dict[str, Any]:
    prompt = (
        f"{context}\n\n"
        "Extract team matchup info. team_a and team_b are named in the context above. "
        "Respond with ONLY a JSON object, no other text:\n"
        '{"team_a_rank": <number or null>, "team_a_name": "<team_a school>", "team_a_mascot": "<mascot>", '
        '"team_b_name": "<team_b school>", "team_b_mascot": "<mascot>", '
        '"team_b_rank": <number or null>, "game_context": "<e.g. Regular Season, Final Four>"}'
    )
    raw = converse_text(prompt, max_tokens=384)
    return _load_json_object(
        raw,
        {
            "team_a_rank": None,
            "team_a_name": "Team A",
            "team_a_mascot": "",
            "team_b_name": "Team B",
            "team_b_mascot": "",
            "team_b_rank": None,
            "game_context": "Matchup",
        },
    )


def generate_win_probability(context: str) -> float:
    prompt = (
        f"{context}\n\n"
        "Based solely on the scout data, analyst findings, and FACTUAL ESPN STATS above, "
        "estimate team_a's win probability as a float from 0 to 100. "
        "Ground the estimate in the actual stat advantages and disadvantages shown — do not guess. "
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
            "Each entry has 'stat', 'team_a', and 'team_b' fields from ESPN. "
            "team_a_pct must be computed from the two real values (team_a / (team_a + team_b)), clamped to [0.0, 1.0].\n\n"
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
        'Respond with ONLY a JSON array. Each element: "label" (string), "team_a_value" (string), "team_b_value" (string), "team_a_pct" (float 0.0-1.0).'
    )
    return _normalize_stat_comparison_items(
        _load_json_array(converse_text(prompt, max_tokens=1024))
    )


def generate_report_cards(context: str, stat_comparison_table: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    if stat_comparison_table:
        table_json = json.dumps(stat_comparison_table)
        table_note = (
            f"AVAILABLE STATS (these are the ONLY stats you have — do not invent any others):\n{table_json}\n\n"
            "Each entry has 'stat', 'team_a', and 'team_b' fields.\n\n"
        )
    else:
        table_note = ""
    prompt = (
        f"{context}\n\n"
        f"{table_note}"
        "Grade BOTH team_a and team_b for dimensions where you have a directly relevant stat in the list above. "
        "For example: only grade 'Scoring' if a points-per-game stat is present, only grade 'Rebounding' if a rebounds stat is present. "
        "Do NOT create a dimension if the relevant stat is absent — omit it entirely. "
        "Grades must be one of A+, A, A-, B+, B, B-, C+, C. "
        "Each item must have: team ('team_a' or 'team_b'), dimension, grade, stat (copy the exact value from the available stats), explanation (1 sentence). "
        "Respond with ONLY a JSON array, no other text."
    )
    raw = _load_json_array(converse_text(prompt, max_tokens=1024))
    # Filter out any card where stat is missing/placeholder or team is not team_a/team_b
    valid = []
    null_values = {"none", "-", "", "null", "n/a", "unknown"}
    for item in raw:
        stat_val = str(item.get("stat") or "").strip().lower()
        if stat_val in null_values:
            continue
        team_val = str(item.get("team") or "").strip().lower()
        if team_val not in {"team_a", "team_b"}:
            continue
        valid.append(item)
    return valid


def generate_matchup_preview(context: str) -> str:
    prompt = (
        f"{context}\n\n"
        "Write a thorough matchup preview for serious fans of these two teams. "
        "Use 3 short paragraphs with 2-3 sentences each and separate each paragraph with a blank line. "
        "Any statistics you cite must come from the FACTUAL ESPN STATS section — do not invent percentages, averages, or rankings. "
        "Include rotation context, recent form, rebounding or turnover dynamics, and matchup angles supported by the data. "
        "Plain text only."
    )
    return converse_text(prompt, max_tokens=512)


def generate_key_factors(context: str) -> list[dict[str, Any]]:
    prompt = (
        f"{context}\n\n"
        "Identify 3-4 key swing factors drawn only from the context and FACTUAL ESPN STATS above. "
        "Any numbers cited in the detail must come from the FACTUAL ESPN STATS — do not invent figures. "
        "Every factor must clearly favor team_a or team_b — pick a side, do not be neutral. "
        'Respond with ONLY a JSON array. Each element: {"label": "<specific factor name>", "detail": "<1 sentence explanation>", "favors": "team_a" or "team_b"}. '
        "Labels must be specific (e.g. 'Rebounding Edge') — never generic like 'Key Factor'."
    )
    raw = converse_text(prompt, max_tokens=768)
    items = _load_json_array(raw)
    result: list[dict[str, Any]] = []
    for item in items:
        label = str(item.get("label", "")).strip()
        detail = str(item.get("detail", "")).strip()
        favors = str(item.get("favors", "team_a")).strip().lower()
        if not label or not detail:
            continue
        if favors not in {"team_a", "team_b"}:
            favors = "team_a"
        result.append({"label": label, "detail": detail, "favors": favors})
    return result[:4]


def generate_prediction(context: str, win_probability: float) -> str:
    prompt = (
        f"{context}\n\n"
        f"Use this exact win probability for team_a: {win_probability:.1f}%.\n"
        "Give a game prediction in 2 short paragraphs separated by a blank line. "
        "The first paragraph states the predicted outcome and score. "
        "The second paragraph explains why, citing only statistics from the FACTUAL ESPN STATS section — do not invent figures. "
        "Do not use a different probability. Plain text only."
    )
    return converse_text(prompt, max_tokens=512)


def _merge_team_header(
    generated: dict[str, Any],
    team_header: dict[str, Any] | None,
) -> dict[str, Any]:
    if not team_header:
        return generated

    merged = dict(generated)
    for key in ("team_a_rank", "team_b_rank"):
        if team_header.get(key) is not None:
            merged[key] = team_header[key]

    for key in ("team_a_name", "team_a_mascot", "team_a_color", "team_b_name", "team_b_mascot", "team_b_color"):
        if team_header.get(key):
            merged[key] = team_header[key]

    if team_header.get("game_context"):
        merged["game_context"] = team_header["game_context"]

    return merged


def run_narrator(
    scout_summary: str,
    analyst_summary: str,
    emit: Emitter,
    team_header: dict[str, Any] | None = None,
    stat_table: list[dict[str, Any]] | None = None,
    team_a_name: str = "Team A",
    team_b_name: str = "Team B",
) -> None:
    emit(events.agent_thought("narrator", f"Generating BI report for {team_a_name} vs {team_b_name}"))
    stat_block = (
        f"\n\nFACTUAL ESPN STATS (cite ONLY these numbers — do not invent any statistics):\n"
        f"{json.dumps(stat_table)}"
        if stat_table
        else ""
    )
    context = (
        f"Matchup: {team_a_name} (team_a) vs {team_b_name} (team_b)\n\n"
        f"Scout data:\n{scout_summary}\n\n"
        f"Analyst findings:\n{analyst_summary}"
        f"{stat_block}"
    )

    # Run all independent LLM calls in parallel; prediction waits for win_probability
    tasks = {
        "insight": lambda: generate_insight_card(context),
        "header": lambda: generate_team_header(context),
        "win_prob": lambda: generate_win_probability(context),
        "stat_comparisons": lambda: generate_stat_comparisons(context, stat_table),
        "report_cards": lambda: generate_report_cards(context, stat_table),
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
    emit(events.insight_card(insight.get("title", "Matchup Insights"), insight.get("data", {})))

    header = _merge_team_header(results.get("header") or {}, team_header)
    emit(
        events.team_header(
            header.get("team_a_rank"),
            str(header.get("team_a_name", "Team A")),
            str(header.get("team_a_mascot", "")),
            str(header.get("team_b_name", "Team B")),
            str(header.get("team_b_mascot", "")),
            header.get("team_b_rank"),
            str(header.get("game_context", "Matchup")),
            team_a_color=header.get("team_a_color"),
            team_b_color=header.get("team_b_color"),
        )
    )

    win_probability: float = results.get("win_prob") or 50.0
    emit(events.win_probability(win_probability))

    for item in results.get("stat_comparisons") or []:
        try:
            pct = float(item.get("team_a_pct", 0.5))
        except (TypeError, ValueError):
            pct = 0.5
        emit(
            events.stat_comparison(
                str(item.get("label", "Stat")),
                str(item.get("team_a_value", "-")),
                str(item.get("team_b_value", "-")),
                max(0.0, min(1.0, pct)),
            )
        )

    _null_stat_values = {"none", "-", "", "null", "n/a", "unknown"}
    for item in results.get("report_cards") or []:
        stat_val = str(item.get("stat") or "").strip().lower()
        if stat_val in _null_stat_values:
            continue
        team_val = str(item.get("team") or "").strip().lower()
        if team_val not in {"team_a", "team_b"}:
            continue
        emit(
            events.report_card(
                team_val,
                str(item.get("dimension", "Dimension")),
                str(item.get("grade", "B")),
                str(item.get("stat", "")),
                str(item.get("explanation", "")),
            )
        )

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
