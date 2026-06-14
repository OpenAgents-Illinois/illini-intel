from app.models import events


def test_team_header_event_uses_team_a_team_b_fields() -> None:
    event = events.team_header(
        3, "Illinois", "Fighting Illini", "UConn", "Huskies", 2, "Final Four",
        team_a_color="ff5f05", team_b_color="0c2340",
    )
    assert event == {
        "type": "team_header",
        "team_a_rank": 3,
        "team_a_name": "Illinois",
        "team_a_mascot": "Fighting Illini",
        "team_a_color": "ff5f05",
        "team_b_name": "UConn",
        "team_b_mascot": "Huskies",
        "team_b_rank": 2,
        "team_b_color": "0c2340",
        "game_context": "Final Four",
    }


def test_stat_comparison_event_uses_team_a_team_b_fields() -> None:
    assert events.stat_comparison("Tempo", "73.1", "69.4", 0.57) == {
        "type": "stat_comparison",
        "label": "Tempo",
        "team_a_value": "73.1",
        "team_b_value": "69.4",
        "team_a_pct": 0.57,
    }


def test_report_card_event_carries_team_tag() -> None:
    assert events.report_card("team_b", "Defense", "A-", "0.42 OppFG%", "Locks down") == {
        "type": "report_card",
        "team": "team_b",
        "dimension": "Defense",
        "grade": "A-",
        "stat": "0.42 OppFG%",
        "explanation": "Locks down",
    }


def test_win_probability_event_is_team_a_probability() -> None:
    assert events.win_probability(61.0) == {
        "type": "win_probability",
        "team_a_probability": 61.0,
    }


def test_key_factor_favors_team_side() -> None:
    assert events.key_factor("Rebounding Edge", "Wins the glass", "team_a") == {
        "type": "key_factor",
        "label": "Rebounding Edge",
        "detail": "Wins the glass",
        "favors": "team_a",
    }


def test_chart_event_removed() -> None:
    assert not hasattr(events, "chart")


def test_done_event_is_terminal_marker() -> None:
    assert events.done() == {"type": "done"}
