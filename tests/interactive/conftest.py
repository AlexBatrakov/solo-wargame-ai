from __future__ import annotations

from pathlib import Path

import pytest

from solo_wargame_ai.io.mission_loader import load_mission

MISSION_PATH = (
    Path(__file__).resolve().parents[2]
    / "configs"
    / "missions"
    / "mission_01_secure_the_woods_1.toml"
)


@pytest.fixture
def mission():
    return load_mission(MISSION_PATH)
