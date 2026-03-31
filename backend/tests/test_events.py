from app.models import events


def test_team_header_event_preserves_structured_fields() -> None:
    event = events.team_header(3, 'Illinois', 'Fighting Illini', 'UConn', 'Huskies', 2, 'Final Four')

    assert event == {
        'type': 'team_header',
        'illinois_rank': 3,
        'illinois_name': 'Illinois',
        'illinois_mascot': 'Fighting Illini',
        'opponent_name': 'UConn',
        'opponent_mascot': 'Huskies',
        'opponent_rank': 2,
        'game_context': 'Final Four',
    }


def test_stat_comparison_event_keeps_frontend_shape() -> None:
    event = events.stat_comparison('Tempo', '73.1', '69.4', 0.57)

    assert event == {
        'type': 'stat_comparison',
        'label': 'Tempo',
        'illinois_value': '73.1',
        'opponent_value': '69.4',
        'illinois_pct': 0.57,
    }


def test_done_event_is_terminal_marker() -> None:
    assert events.done() == {'type': 'done'}
