from app.services.narrator import _extract_json_array, _extract_json_object, _merge_team_header


def test_extract_json_object_handles_code_fences() -> None:
    raw = '```json\n{"title": "Test", "data": {"wins": "10"}}\n```'
    assert _extract_json_object(raw) == '{"title": "Test", "data": {"wins": "10"}}'


def test_extract_json_array_handles_code_fences() -> None:
    raw = '```json\n[{"label": "Pace"}]\n```'
    assert _extract_json_array(raw) == '[{"label": "Pace"}]'


def test_merge_team_header_prefers_structured_ranks() -> None:
    generated = {
        'team_a_rank': None,
        'team_a_name': 'Illinois',
        'team_a_mascot': 'Fighting Illini',
        'team_b_name': 'Connecticut',
        'team_b_mascot': 'Huskies',
        'team_b_rank': None,
        'game_context': 'Final Four',
    }
    structured = {
        'team_a_rank': 3,
        'team_a_name': 'Illinois',
        'team_a_mascot': 'Fighting Illini',
        'team_b_name': 'UConn',
        'team_b_mascot': 'Huskies',
        'team_b_rank': 2,
    }

    assert _merge_team_header(generated, structured) == {
        'team_a_rank': 3,
        'team_a_name': 'Illinois',
        'team_a_mascot': 'Fighting Illini',
        'team_b_name': 'UConn',
        'team_b_mascot': 'Huskies',
        'team_b_rank': 2,
        'game_context': 'Final Four',
    }
