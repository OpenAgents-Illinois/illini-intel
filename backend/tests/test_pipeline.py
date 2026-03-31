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
                'team': {'displayName': 'Illinois'},
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
        return {
            'team': {'displayName': 'UConn'},
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

    monkeypatch.setattr(pipeline, 'fetch_team', fake_fetch_team)
    monkeypatch.setattr(pipeline, 'fetch_schedule', lambda team_id: {'events': [1, 2, 3]})
    monkeypatch.setattr(pipeline, 'fetch_scoreboard', lambda: {'events': [1]})

    def fake_converse_text(prompt: str, max_tokens: int = 1024) -> str:
        if 'Scout summary:' in prompt:
            return 'Analyst sees Illinois spacing advantage.'
        return 'Scout summary for Illinois.'

    narrator_calls = []

    def fake_run_narrator(goal: str, scout_summary: str, analyst_summary: str, emit, team_header=None):
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
            {'illinois_rank': 3, 'opponent_name': 'UConn', 'opponent_rank': 2},
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
