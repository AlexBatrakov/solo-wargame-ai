from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from solo_wargame_ai.domain.actions import ChooseOrderExecutionAction, OrderExecutionChoice
from solo_wargame_ai.domain.decision_context import ChooseOrderExecutionContext
from solo_wargame_ai.domain.enums import HexDirection
from solo_wargame_ai.domain.hexgrid import HexCoord
from solo_wargame_ai.domain.legal_actions import get_legal_actions
from solo_wargame_ai.domain.mission import HiddenMarker
from solo_wargame_ai.domain.state import CurrentActivation, create_initial_game_state
from solo_wargame_ai.domain.units import BritishMorale, GermanUnitStatus, RevealedGermanUnitState
from solo_wargame_ai.io.mission_loader import load_mission

MISSION_PATH = (
    Path(__file__).resolve().parents[1]
    / "configs"
    / "missions"
    / "mission_01_secure_the_woods_1.toml"
)


def test_order_execution_excludes_fire_dead_ends_but_keeps_valid_alternatives() -> None:
    state = _state_at_choose_order_execution(selected_die=4)

    assert get_legal_actions(state) == (
        ChooseOrderExecutionAction(choice=OrderExecutionChoice.SECOND_ORDER_ONLY),
        ChooseOrderExecutionAction(choice=OrderExecutionChoice.NO_ACTION),
    )


def test_order_execution_excludes_advance_dead_ends_when_no_forward_destination_exists() -> None:
    mission = _mission_with_hidden_markers(
        HiddenMarker(marker_id="qm_1", coord=HexCoord(-1, 2)),
        HiddenMarker(marker_id="qm_2", coord=HexCoord(0, 1)),
        HiddenMarker(marker_id="qm_3", coord=HexCoord(1, 1)),
    )
    state = _state_at_choose_order_execution(
        mission=mission,
        selected_die=3,
        active_position=HexCoord(0, 2),
        german_units={
            "qm_1": _german_unit("qm_1", HexCoord(-1, 2)),
            "qm_2": _german_unit("qm_2", HexCoord(0, 1)),
            "qm_3": _german_unit("qm_3", HexCoord(1, 1)),
        },
    )

    assert get_legal_actions(state) == (
        ChooseOrderExecutionAction(choice=OrderExecutionChoice.SECOND_ORDER_ONLY),
        ChooseOrderExecutionAction(choice=OrderExecutionChoice.NO_ACTION),
    )


def test_order_execution_preserves_low_morale_filtering_after_dead_end_pruning() -> None:
    state = _state_at_choose_order_execution(
        selected_die=4,
        active_morale=BritishMorale.LOW,
    )

    assert get_legal_actions(state) == (
        ChooseOrderExecutionAction(choice=OrderExecutionChoice.NO_ACTION),
    )


def _mission_with_hidden_markers(*markers: HiddenMarker):
    mission = load_mission(MISSION_PATH)
    return replace(
        mission,
        map=replace(mission.map, hidden_markers=markers),
    )


def _state_at_choose_order_execution(
    *,
    mission=None,
    selected_die: int,
    active_position: HexCoord = HexCoord(0, 3),
    active_morale: BritishMorale = BritishMorale.NORMAL,
    german_units: dict[str, RevealedGermanUnitState] | None = None,
):
    if mission is None:
        mission = load_mission(MISSION_PATH)

    base_state = create_initial_game_state(mission)
    british_units = dict(base_state.british_units)
    british_units["rifle_squad_a"] = replace(
        british_units["rifle_squad_a"],
        position=active_position,
        morale=active_morale,
    )

    return replace(
        base_state,
        british_units=british_units,
        german_units={} if german_units is None else german_units,
        unresolved_markers={
            marker_id: marker_state
            for marker_id, marker_state in base_state.unresolved_markers.items()
            if german_units is None or marker_id not in german_units
        },
        pending_decision=ChooseOrderExecutionContext(),
        current_activation=CurrentActivation(
            active_unit_id="rifle_squad_a",
            roll=(selected_die, 1 if selected_die != 1 else 2),
            selected_die=selected_die,
        ),
    )


def _german_unit(
    unit_id: str,
    position: HexCoord,
    *,
    facing: HexDirection = HexDirection.DOWN,
    status: GermanUnitStatus = GermanUnitStatus.ACTIVE,
) -> RevealedGermanUnitState:
    return RevealedGermanUnitState(
        unit_id=unit_id,
        unit_class="light_machine_gun",
        position=position,
        facing=facing,
        status=status,
    )
