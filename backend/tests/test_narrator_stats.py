from app.services import narrator


def test_normalize_stat_comparison_items_filters_placeholder_rows() -> None:
    items = [
        {
            "label": "Stat",
            "team_a_value": "87.1",
            "team_b_value": "81.2",
            "team_a_pct": 1.0,
        },
        {
            "label": "Tempo",
            "team_a_value": "73.1",
            "team_b_value": "69.4",
            "team_a_pct": 0.57,
        },
    ]

    assert narrator._normalize_stat_comparison_items(items) == [
        {
            "label": "Tempo",
            "team_a_value": "73.1",
            "team_b_value": "69.4",
            "team_a_pct": 0.57,
        }
    ]


def test_normalize_stat_comparison_items_drops_missing_team_b_value() -> None:
    items = [
        {
            "label": "Tempo",
            "team_a_value": "73.1",
            "team_b_value": "-",
            "team_a_pct": 1.0,
        },
        {
            "label": "Rebounding",
            "team_a_value": "39.0",
            "team_b_value": "31.2",
            "team_a_pct": 0.56,
        },
    ]

    assert narrator._normalize_stat_comparison_items(items) == [
        {
            "label": "Rebounding",
            "team_a_value": "39.0",
            "team_b_value": "31.2",
            "team_a_pct": 0.56,
        }
    ]


def test_generate_stat_comparisons_returns_normalized_items(monkeypatch) -> None:
    monkeypatch.setattr(
        narrator,
        "converse_text",
        lambda prompt, max_tokens=1024: """
        [
          {"label":"Stat","team_a_value":"-","team_b_value":"-","team_a_pct":1.0},
          {"label":"Tempo","team_a_value":"73.1","team_b_value":"69.4","team_a_pct":0.57}
        ]
        """,
    )

    assert narrator.generate_stat_comparisons("Illinois vs UConn") == [
        {
            "label": "Tempo",
            "team_a_value": "73.1",
            "team_b_value": "69.4",
            "team_a_pct": 0.57,
        }
    ]


def test_run_narrator_emits_win_probability_with_team_a_field(monkeypatch) -> None:
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
