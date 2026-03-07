from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from solo_wargame_ai.domain.actions import AdvanceAction
from solo_wargame_ai.domain.decision_context import ChooseOrderParameterContext
from solo_wargame_ai.domain.enums import HexDirection
from solo_wargame_ai.domain.hexgrid import HexCoord
from solo_wargame_ai.domain.legal_actions import apply_action
from solo_wargame_ai.domain.mission import HiddenMarker, OrderName
from solo_wargame_ai.domain.state import CurrentActivation, create_initial_game_state
from solo_wargame_ai.io.mission_loader import load_mission

MISSION_PATH = (
    Path(__file__).resolve().parents[1]
    / "configs"
    / "missions"
    / "mission_01_secure_the_woods_1.toml"
)


def test_movement_reveal_removes_marker_and_creates_revealed_german() -> None:
    state = _stage_advance_state(seed=0)

    next_state = apply_action(state, AdvanceAction(destination=HexCoord(0, 2)))

    assert "qm_1" not in next_state.unresolved_markers
    assert next_state.german_units["qm_1"].unit_class == "light_machine_gun"
    assert next_state.german_units["qm_1"].position == HexCoord(0, 1)
    assert next_state.german_units["qm_1"].facing is HexDirection.DOWN


def test_movement_reveal_uses_rng_deterministically() -> None:
    first_state = _stage_advance_state(seed=1)
    second_state = _stage_advance_state(seed=1)

    first_result = apply_action(first_state, AdvanceAction(destination=HexCoord(0, 2)))
    second_result = apply_action(second_state, AdvanceAction(destination=HexCoord(0, 2)))

    assert first_result.german_units == second_result.german_units
    assert first_result.rng_state == second_result.rng_state
    assert first_result.german_units["qm_1"].unit_class == "heavy_machine_gun"


def test_movement_reveal_reveals_all_adjacent_markers_from_one_destination() -> None:
    mission = _mission_with_hidden_markers(
        HiddenMarker(marker_id="qm_1", coord=HexCoord(0, 1)),
        HiddenMarker(marker_id="qm_2", coord=HexCoord(1, 1)),
    )
    state = _stage_advance_state(mission=mission, seed=0)

    next_state = apply_action(state, AdvanceAction(destination=HexCoord(0, 2)))

    assert next_state.unresolved_markers == {}
    assert set(next_state.german_units) == {"qm_1", "qm_2"}
    assert next_state.german_units["qm_1"].unit_class == "light_machine_gun"
    assert next_state.german_units["qm_1"].facing is HexDirection.DOWN
    assert next_state.german_units["qm_2"].unit_class == "light_machine_gun"
    assert next_state.german_units["qm_2"].position == HexCoord(1, 1)
    assert next_state.german_units["qm_2"].facing is HexDirection.DOWN_LEFT


def _mission_with_hidden_markers(*markers: HiddenMarker):
    mission = load_mission(MISSION_PATH)
    return replace(
        mission,
        map=replace(
            mission.map,
            hidden_markers=markers,
        ),
    )


def _stage_advance_state(*, mission=None, seed: int = 0):
    if mission is None:
        mission = load_mission(MISSION_PATH)

    base_state = create_initial_game_state(mission, seed=seed)
    return replace(
        base_state,
        pending_decision=ChooseOrderParameterContext(
            order=OrderName.ADVANCE,
            order_index=0,
        ),
        current_activation=CurrentActivation(
            active_unit_id="rifle_squad_a",
            roll=(6, 1),
            selected_die=6,
            planned_orders=(OrderName.ADVANCE,),
            next_order_index=0,
        ),
    )
