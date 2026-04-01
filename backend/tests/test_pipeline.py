from __future__ import annotations

from app.services import pipeline


class RecordingEmitter:
    def __init__(self) -> None:
        self.events = []

    def __call__(self, event):
        self.events.append(event)


def test_pipeline_emits_done_when_upstream_fails(monkeypatch) -> None:
    emitter = RecordingEmitter()

    def fail_fetch_team(team_id: str):
        raise RuntimeError('espn unavailable')

    monkeypatch.setattr(pipeline, 'fetch_team', fail_fetch_team)

    pipeline.run('Analyze Illinois vs UConn', emitter)

    assert emitter.events[0]['type'] == 'agent_thought'
    assert any(event['type'] == 'agent_thought' and event['agent'] == 'scout' and 'Scout error' in event['content'] for event in emitter.events)
    assert any(event['type'] == 'agent_thought' and event['agent'] == 'narrator' and 'Skipping narrator' in event['content'] for event in emitter.events)
    assert emitter.events[-1] == {'type': 'done'}


def test_pipeline_runs_narrator_after_successful_scout_and_analyst(monkeypatch) -> None:
    emitter = RecordingEmitter()

    def fake_fetch_team(team_id: str):
        if team_id == '356':
            return {
                'team': {
                    'displayName': 'Illinois',
                    'shortDisplayName': 'Illinois',
                    'name': 'Fighting Illini',
                },
                'nextEvent': [
                    {
                        'competitions': [
                            {
                                'competitors': [
                                    {'team': {'id': '356'}, 'curatedRank': {'current': 3}},
                                ]
                            }
                        ]
                    }
                ],
            }
        if team_id == '41':
            return {
                'team': {
                    'displayName': 'UConn Huskies',
                    'shortDisplayName': 'UConn',
                    'name': 'Huskies',
                    'location': 'Connecticut',
                }
            }
        return {
            'team': {'displayName': 'Opponent'},
        }

    monkeypatch.setattr(pipeline, 'fetch_team', fake_fetch_team)
    monkeypatch.setattr(
        pipeline,
        'fetch_schedule',
        lambda team_id, season=None: {
            'events': [
                {
                    'name': 'Illinois vs UConn',
                    'season': {'year': 2024},
                    'competitions': [
                        {
                            'notes': [{'headline': "Men's Basketball Championship - East Region - Elite 8"}],
                            'competitors': [
                                {'team': {'id': '356', 'shortDisplayName': 'Illinois', 'name': 'Fighting Illini'}, 'curatedRank': {'current': 3}},
                                {'team': {'id': '41', 'shortDisplayName': 'UConn', 'name': 'Huskies'}, 'curatedRank': {'current': 2}},
                            ],
                        }
                    ],
                }
            ]
        },
    )
    monkeypatch.setattr(pipeline, 'fetch_scoreboard', lambda: {'events': [1]})

    def fake_converse_text(prompt: str, max_tokens: int = 1024) -> str:
        if 'Scout summary:' in prompt:
            return 'Analyst sees Illinois spacing advantage.'
        return 'Scout summary for Illinois.'

    narrator_calls = []

    def fake_run_narrator(goal: str, scout_summary: str, analyst_summary: str, emit, team_header=None, stat_comparison_table=None):
        narrator_calls.append((goal, scout_summary, analyst_summary, team_header))
        emit({'type': 'prediction', 'content': 'Illinois 78-74'})

    monkeypatch.setattr(pipeline, 'converse_text', fake_converse_text)
    monkeypatch.setattr(pipeline, 'run_narrator', fake_run_narrator)

    pipeline.run('Analyze Illinois vs UConn', emitter)

    assert narrator_calls == [
        (
            'Analyze Illinois vs UConn',
            'Scout summary for Illinois.',
            'Analyst sees Illinois spacing advantage.',
            {
                'illinois_rank': 3,
                'illinois_name': 'Illinois',
                'illinois_mascot': 'Fighting Illini',
                'illinois_color': None,
                'opponent_name': 'UConn',
                'opponent_mascot': 'Huskies',
                'opponent_rank': 2,
                'opponent_color': None,
                'game_context': 'Elite 8',
            },
        )
    ]
    assert any(event['type'] == 'tool_call' and event['tool'] == 'fetch_scoreboard' for event in emitter.events)
    assert any(event['type'] == 'prediction' for event in emitter.events)
    assert emitter.events[-1] == {'type': 'done'}


def test_extract_ap_rank_prefers_curated_rank_over_top_level_rank() -> None:
    payload = {
        'rank': 13,
        'nextEvent': [
            {
                'competitions': [
                    {
                        'competitors': [
                            {'team': {'id': '356'}, 'curatedRank': {'current': 3}},
                        ]
                    }
                ]
            }
        ],
    }

    assert pipeline._extract_ap_rank(payload, '356') == 3


def test_extract_ap_rank_falls_back_to_top_level_rank() -> None:
    payload = {'rank': 7}

    assert pipeline._extract_ap_rank(payload, '41') == 7


def test_extract_ap_rank_handles_nested_team_rank_strings() -> None:
    payload = {
        'team': {'rank': '#13'},
        'nextEvent': [],
    }

    assert pipeline._extract_ap_rank(payload, '356') == 13


def test_build_team_header_uses_structured_espn_data() -> None:
    illinois = {
        'team': {
            'displayName': 'Illinois',
            'shortDisplayName': 'Illinois',
            'name': 'Fighting Illini',
        },
        'nextEvent': [
            {
                'competitions': [
                    {
                        'competitors': [
                            {'team': {'id': '356'}, 'curatedRank': {'current': 3}},
                        ]
                    }
                ]
            }
        ],
    }
    opponent = {
        'team': {
            'displayName': 'UConn Huskies',
            'shortDisplayName': 'UConn',
            'name': 'Huskies',
            'location': 'Connecticut',
        },
        'nextEvent': [
            {
                'competitions': [
                    {
                        'competitors': [
                            {'team': {'id': '41'}, 'curatedRank': {'current': 2}},
                        ]
                    }
                ]
            }
        ],
    }

    assert pipeline._build_team_header(illinois, opponent) == {
        'illinois_rank': 3,
        'illinois_name': 'Illinois',
        'illinois_mascot': 'Fighting Illini',
        'illinois_color': None,
        'opponent_name': 'UConn',
        'opponent_mascot': 'Huskies',
        'opponent_rank': 2,
        'opponent_color': None,
        'game_context': None,
    }


def test_build_team_header_uses_matchup_event_context_and_opponent() -> None:
    matchup_event = {
        'competitions': [
            {
                'notes': [{'headline': "Men's Basketball Championship - East Region - Elite 8"}],
                'competitors': [
                    {'team': {'id': '356', 'shortDisplayName': 'Illinois', 'name': 'Fighting Illini'}, 'curatedRank': {'current': 3}},
                    {'team': {'id': '41', 'shortDisplayName': 'UConn', 'name': 'Huskies'}, 'curatedRank': {'current': 2}},
                ],
            }
        ]
    }

    assert pipeline._build_team_header({'team': {}}, {'team': {}}, matchup_event) == {
        'illinois_rank': 3,
        'illinois_name': 'Illinois',
        'illinois_mascot': 'Fighting Illini',
        'illinois_color': None,
        'opponent_name': 'UConn',
        'opponent_mascot': 'Huskies',
        'opponent_rank': 2,
        'opponent_color': None,
        'game_context': 'Elite 8',
    }
