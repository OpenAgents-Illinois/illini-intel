from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint_returns_ok() -> None:
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.text == "ok"


def test_leagues_endpoint_lists_registry() -> None:
    response = TestClient(app).get("/leagues")
    assert response.status_code == 200
    keys = {item["key"] for item in response.json()}
    assert {"mens-college-basketball", "nba"} <= keys


def test_analyze_passes_structured_request(monkeypatch) -> None:
    seen = {}

    def fake_run_pipeline(request, emit):
        seen["req"] = request
        emit({"type": "done"})

    monkeypatch.setattr("app.api.routes.run_pipeline", fake_run_pipeline)
    response = TestClient(app).get("/analyze", params={"league": "nba", "team_a": "13", "team_b": "2"})

    assert response.status_code == 200
    assert (seen["req"].league_key, seen["req"].team_a_id, seen["req"].team_b_id) == ("nba", "13", "2")
    assert '"type": "done"' in response.text


def test_analyze_defaults_to_illini_matchup(monkeypatch) -> None:
    seen = {}

    def fake_run_pipeline(request, emit):
        seen["req"] = request
        emit({"type": "done"})

    monkeypatch.setattr("app.api.routes.run_pipeline", fake_run_pipeline)
    TestClient(app).get("/analyze")

    assert (seen["req"].league_key, seen["req"].team_a_id, seen["req"].team_b_id) == (
        "mens-college-basketball", "356", "41",
    )


def test_analyze_rejects_equal_teams() -> None:
    response = TestClient(app).get("/analyze", params={"league": "nba", "team_a": "13", "team_b": "13"})
    assert response.status_code == 200
    assert "must be different" in response.text
    assert '"type": "done"' in response.text


def test_teams_endpoint_returns_options(monkeypatch) -> None:
    def fake_fetch_teams(league):
        return {"sports": [{"leagues": [{"teams": [
            {"team": {"id": "13", "displayName": "Los Angeles Lakers"}},
            {"team": {"id": "2", "displayName": "Boston Celtics"}},
        ]}]}]}

    monkeypatch.setattr("app.api.routes.fetch_teams", fake_fetch_teams)
    response = TestClient(app).get("/teams", params={"league": "nba"})

    assert response.status_code == 200
    assert {"id": "13", "name": "Los Angeles Lakers"} in response.json()
