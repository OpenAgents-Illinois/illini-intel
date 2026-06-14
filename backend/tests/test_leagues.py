from __future__ import annotations

from app.core import leagues


def test_get_league_returns_known_league() -> None:
    league = leagues.get_league("nba")
    assert league is not None
    assert league.sport == "basketball"
    assert league.path == "basketball/nba"
    assert league.label == "NBA"


def test_get_league_returns_none_for_unknown_key() -> None:
    assert leagues.get_league("quidditch") is None


def test_every_registry_entry_is_well_formed() -> None:
    for key, league in leagues.LEAGUES.items():
        assert league.key == key
        assert league.sport
        assert league.path.startswith(f"{league.sport}/")
        assert league.label


def test_default_league_is_registered() -> None:
    assert "mens-college-basketball" in leagues.LEAGUES
