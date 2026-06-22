from __future__ import annotations

from app.core import config


def test_matchup_defaults_present() -> None:
    assert config.DEFAULT_LEAGUE == "mens-college-basketball"
    assert config.DEFAULT_TEAM_A == "356"   # Illinois
    assert config.DEFAULT_TEAM_B == "41"    # UConn


def test_legacy_constants_removed() -> None:
    for name in ("ILLINOIS_TEAM_ID", "UCONN_TEAM_ID", "ESPN_BASE_URL", "DEFAULT_GOAL"):
        assert not hasattr(config, name), f"{name} should be removed"
