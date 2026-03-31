from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint_returns_ok() -> None:
    client = TestClient(app)
    response = client.get('/health')

    assert response.status_code == 200
    assert response.text == 'ok'


def test_analyze_stream_emits_sse_events(monkeypatch) -> None:
    def fake_run_pipeline(goal, emit):
        assert goal == 'Analyze Illinois vs UConn'
        emit({'type': 'agent_thought', 'agent': 'scout', 'content': 'starting'})
        emit({'type': 'insight_card', 'title': 'Keys', 'data': {'pace': 'fast'}})
        emit({'type': 'done'})

    monkeypatch.setattr('app.api.routes.run_pipeline', fake_run_pipeline)

    client = TestClient(app)
    response = client.get('/analyze', params={'goal': 'Analyze Illinois vs UConn'})

    assert response.status_code == 200
    assert response.headers['content-type'].startswith('text/event-stream')
    assert '"type": "agent_thought"' in response.text
    assert '"type": "insight_card"' in response.text
    assert '"type": "done"' in response.text


def test_analyze_stream_emits_done_on_pipeline_error(monkeypatch) -> None:
    def fake_run_pipeline(goal, emit):
        raise RuntimeError('boom')

    monkeypatch.setattr('app.api.routes.run_pipeline', fake_run_pipeline)

    client = TestClient(app)
    response = client.get('/analyze')

    assert response.status_code == 200
    assert 'Server error' in response.text
    assert '"type": "done"' in response.text
