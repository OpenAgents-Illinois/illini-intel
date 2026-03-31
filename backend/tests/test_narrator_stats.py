from app.services import narrator


def test_normalize_stat_comparison_items_filters_placeholder_rows() -> None:
    items = [
        {
            "label": "Stat",
            "illinois_value": "87.1",
            "opponent_value": "81.2",
            "illinois_pct": 1.0,
        },
        {
            "label": "Tempo",
            "illinois_value": "73.1",
            "opponent_value": "69.4",
            "illinois_pct": 0.57,
        },
    ]

    assert narrator._normalize_stat_comparison_items(items) == [
        {
            "label": "Tempo",
            "illinois_value": "73.1",
            "opponent_value": "69.4",
            "illinois_pct": 0.57,
        }
    ]


def test_normalize_stat_comparison_items_drops_all_extreme_rows() -> None:
    items = [
        {
            "label": "Tempo",
            "illinois_value": "73.1",
            "opponent_value": "69.4",
            "illinois_pct": 1.0,
        },
        {
            "label": "Rebounding",
            "illinois_value": "39.0",
            "opponent_value": "31.2",
            "illinois_pct": 1.0,
        },
        {
            "label": "Turnovers",
            "illinois_value": "10.2",
            "opponent_value": "13.4",
            "illinois_pct": 1.0,
        },
    ]

    assert narrator._normalize_stat_comparison_items(items) == []


def test_generate_stat_comparisons_returns_normalized_items(monkeypatch) -> None:
    monkeypatch.setattr(
        narrator,
        "converse_text",
        lambda prompt, max_tokens=1024: """
        [
          {"label":"Stat","illinois_value":"-","opponent_value":"-","illinois_pct":1.0},
          {"label":"Tempo","illinois_value":"73.1","opponent_value":"69.4","illinois_pct":0.57}
        ]
        """,
    )

    assert narrator.generate_stat_comparisons("Illinois vs UConn") == [
        {
            "label": "Tempo",
            "illinois_value": "73.1",
            "opponent_value": "69.4",
            "illinois_pct": 0.57,
        }
    ]
