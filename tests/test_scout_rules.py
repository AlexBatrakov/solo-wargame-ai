from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from solo_wargame_ai.domain.actions import ScoutAction
from solo_wargame_ai.domain.decision_context import ChooseOrderParameterContext
from solo_wargame_ai.domain.enums import HexDirection
from solo_wargame_ai.domain.hexgrid import HexCoord
from solo_wargame_ai.domain.legal_actions import apply_action, get_legal_actions
from solo_wargame_ai.domain.mission import HiddenMarker, OrderName
from solo_wargame_ai.domain.state import CurrentActivation, create_initial_game_state
from solo_wargame_ai.io.mission_loader import load_mission

MISSION_PATH = (
    Path(__file__).resolve().parents[1]
    / "configs"
    / "missions"
    / "mission_01_secure_the_woods_1.toml"
)


def test_scout_targets_only_markers_exactly_two_hexes_away() -> None:
    state = _stage_scout_state(active_position=HexCoord(0, 3))

    assert get_legal_actions(state) == (
        ScoutAction(marker_id="qm_1", facing=HexDirection.DOWN_LEFT),
        ScoutAction(marker_id="qm_1", facing=HexDirection.DOWN),
        ScoutAction(marker_id="qm_1", facing=HexDirection.DOWN_RIGHT),
    )

    adjacent_state = _stage_scout_state(active_position=HexCoord(0, 2))

    assert get_legal_actions(adjacent_state) == ()


def test_scout_excludes_downward_facings_that_point_directly_off_map() -> None:
    mission = _mission_with_hidden_marker(HiddenMarker(marker_id="qm_1", coord=HexCoord(1, 0)))
    state = _stage_scout_state(
        mission=mission,
        active_position=HexCoord(1, 2),
    )

    assert get_legal_actions(state) == (
        ScoutAction(marker_id="qm_1", facing=HexDirection.DOWN_LEFT),
        ScoutAction(marker_id="qm_1", facing=HexDirection.DOWN),
    )


def test_scout_reveal_uses_chosen_facing_without_moving_the_british_unit() -> None:
    state = _stage_scout_state(
        active_position=HexCoord(1, 2),
        planned_orders=(OrderName.ADVANCE, OrderName.SCOUT),
        next_order_index=1,
        seed=0,
    )

    next_state = apply_action(
        state,
        ScoutAction(marker_id="qm_1", facing=HexDirection.DOWN_RIGHT),
    )

    assert next_state.british_units["rifle_squad_a"].position == HexCoord(1, 2)
    assert "qm_1" not in next_state.unresolved_markers
    assert next_state.german_units["qm_1"].unit_class == "light_machine_gun"
    assert next_state.german_units["qm_1"].facing is HexDirection.DOWN_RIGHT
    assert next_state.current_activation is None
    assert next_state.activated_british_unit_ids == frozenset({"rifle_squad_a"})


def _mission_with_hidden_marker(marker: HiddenMarker):
    mission = load_mission(MISSION_PATH)
    return replace(
        mission,
        map=replace(mission.map, hidden_markers=(marker,)),
    )


def _stage_scout_state(
    *,
    mission=None,
    seed: int = 0,
    active_position: HexCoord = HexCoord(0, 3),
    planned_orders: tuple[OrderName, ...] = (OrderName.SCOUT,),
    next_order_index: int = 0,
):
    if mission is None:
        mission = load_mission(MISSION_PATH)

    base_state = create_initial_game_state(mission, seed=seed)
    british_units = dict(base_state.british_units)
    british_units["rifle_squad_a"] = replace(
        british_units["rifle_squad_a"],
        position=active_position,
    )

    return replace(
        base_state,
        british_units=british_units,
        pending_decision=ChooseOrderParameterContext(
            order=planned_orders[next_order_index],
            order_index=next_order_index,
        ),
        current_activation=CurrentActivation(
            active_unit_id="rifle_squad_a",
            roll=(2, 1),
            selected_die=2,
            planned_orders=planned_orders,
            next_order_index=next_order_index,
        ),
    )
