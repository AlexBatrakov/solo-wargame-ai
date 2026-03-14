from dataclasses import replace
from pathlib import Path

import pytest

from solo_wargame_ai.domain.decision_context import (
    ChooseBritishUnitContext,
    DecisionContextKind,
)
from solo_wargame_ai.domain.hexgrid import HexCoord
from solo_wargame_ai.domain.state import GamePhase, create_initial_game_state, validate_game_state
from solo_wargame_ai.domain.units import BritishMorale
from solo_wargame_ai.io.mission_loader import load_mission

MISSION_PATH = (
    Path(__file__).resolve().parents[1]
    / "configs"
    / "missions"
    / "mission_01_secure_the_woods_1.toml"
)


def test_create_initial_game_state_matches_the_stage_3b_runtime_contract() -> None:
    mission = load_mission(MISSION_PATH)

    state = create_initial_game_state(mission)

    validate_game_state(state)

    assert state.mission is mission
    assert state.turn == 1
    assert state.phase is GamePhase.BRITISH
    assert isinstance(state.pending_decision, ChooseBritishUnitContext)
    assert state.pending_decision.kind is DecisionContextKind.CHOOSE_BRITISH_UNIT
    assert state.activated_british_unit_ids == frozenset()
    assert state.activated_german_unit_ids == frozenset()
    assert state.current_activation is None

    assert tuple(state.british_units) == ("rifle_squad_a", "rifle_squad_b")
    assert {unit.position for unit in state.british_units.values()} == {HexCoord(0, 3)}
    assert {unit.morale for unit in state.british_units.values()} == {BritishMorale.NORMAL}
    assert {unit.cover for unit in state.british_units.values()} == {0}

    assert len(state.german_units) == 0
    assert tuple(state.unresolved_markers) == ("qm_1",)
    assert state.unresolved_markers["qm_1"].position == HexCoord(0, 1)

    assert state.rng_state.seed == 0
    assert len(state.rng_state.internal_state) > 0


def test_create_initial_game_state_keeps_single_start_guard_aligned_with_loader() -> None:
    mission = load_mission(MISSION_PATH)
    broken_map = replace(
        mission.map,
        start_hexes=mission.map.start_hexes + (HexCoord(-1, 3),),
    )

    with pytest.raises(
        ValueError,
        match="Current supported missions require exactly one start hex",
    ):
        create_initial_game_state(replace(mission, map=broken_map))
