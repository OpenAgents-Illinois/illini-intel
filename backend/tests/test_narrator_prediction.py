from app.services import narrator


def test_generate_prediction_uses_exact_structured_probability(monkeypatch) -> None:
    seen_prompt = {}

    def fake_converse_text(prompt: str, max_tokens: int = 512) -> str:
        seen_prompt["prompt"] = prompt
        return "Illinois has a 61.0% win probability and wins 78-74."

    monkeypatch.setattr(narrator, "converse_text", fake_converse_text)

    result = narrator.generate_prediction("Illinois vs UConn", 61.0)

    assert result == "Illinois has a 61.0% win probability and wins 78-74."
    assert "Use this exact win probability for team_a: 61.0%" in seen_prompt["prompt"]
    assert "Do not use a different probability" in seen_prompt["prompt"]
