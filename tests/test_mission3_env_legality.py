from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from solo_wargame_ai.domain.actions import (
    ChooseOrderExecutionAction,
    OrderExecutionChoice,
    SelectActivationDieAction,
    SelectBritishUnitAction,
)
from solo_wargame_ai.domain.decision_context import ChooseGermanUnitContext
from solo_wargame_ai.domain.enums import HexDirection
from solo_wargame_ai.domain.hexgrid import HexCoord
from solo_wargame_ai.domain.resolver import apply_action
from solo_wargame_ai.domain.state import GamePhase, create_initial_game_state
from solo_wargame_ai.domain.units import GermanUnitStatus, RevealedGermanUnitState
from solo_wargame_ai.env.legal_action_mask import (
    IllegalActionIdError,
    build_legal_action_selection,
    decode_legal_action_id,
)
from solo_wargame_ai.env.mission3_action_catalog import build_mission3_action_catalog
from solo_wargame_ai.env.normalized_state import normalize_env_state
from solo_wargame_ai.io.mission_loader import load_mission

MISSION_PATH = (
    Path(__file__).resolve().parents[1]
    / "configs"
    / "missions"
    / "mission_03_secure_the_building.toml"
)


def _initial_state():
    mission = load_mission(MISSION_PATH)
    return create_initial_game_state(mission, seed=0)


def _double_choice_state():
    return apply_action(
        _initial_state(),
        SelectBritishUnitAction(unit_id="rifle_squad_c"),
    )


def _activation_die_state():
    mission = load_mission(MISSION_PATH)
    return apply_action(
        create_initial_game_state(mission, seed=1),
        SelectBritishUnitAction(unit_id="rifle_squad_c"),
    )


def _order_execution_state():
    return apply_action(
        _activation_die_state(),
        SelectActivationDieAction(die_value=2),
    )


def _advance_parameter_state():
    return apply_action(
        _order_execution_state(),
        ChooseOrderExecutionAction(choice=OrderExecutionChoice.FIRST_ORDER_ONLY),
    )


def _german_unit_state():
    mission = load_mission(MISSION_PATH)
    base_state = create_initial_game_state(mission, seed=0)
    return replace(
        base_state,
        phase=GamePhase.GERMAN,
        activated_british_unit_ids=frozenset(base_state.british_units),
        activated_german_unit_ids=frozenset(),
        pending_decision=ChooseGermanUnitContext(),
        current_activation=None,
        unresolved_markers={},
        german_units={
            "qm_1": RevealedGermanUnitState(
                unit_id="qm_1",
                unit_class="light_machine_gun",
                position=HexCoord(-1, 2),
                facing=HexDirection.DOWN,
                status=GermanUnitStatus.ACTIVE,
            ),
        },
    )


@pytest.mark.parametrize(
    ("state_factory", "expected_pending_kind"),
    [
        (_initial_state, "choose_british_unit"),
        (_double_choice_state, "choose_double_choice"),
        (_activation_die_state, "choose_activation_die"),
        (_order_execution_state, "choose_order_execution"),
        (_advance_parameter_state, "choose_order_parameter"),
        (_german_unit_state, "choose_german_unit"),
    ],
    ids=[
        "choose-british-unit",
        "choose-double-choice",
        "choose-activation-die",
        "choose-order-execution",
        "choose-order-parameter-advance",
        "choose-german-unit",
    ],
)
def test_mission3_legal_action_selection_matches_resolver_for_representative_contexts(
    state_factory,
    expected_pending_kind: str,
) -> None:
    mission = load_mission(MISSION_PATH)
    catalog = build_mission3_action_catalog(mission)
    normalized_state = normalize_env_state(state_factory())

    selection = build_legal_action_selection(normalized_state, catalog)

    assert normalized_state.state.pending_decision.kind.value == expected_pending_kind
    expected_ids = tuple(
        action_id
        for action_id in range(catalog.size)
        if catalog.decode(action_id) in normalized_state.legal_actions
    )
    assert selection.legal_action_ids == expected_ids
    assert selection.legal_action_mask == tuple(
        action_id in expected_ids
        for action_id in range(catalog.size)
    )

    for action_id in selection.legal_action_ids:
        assert decode_legal_action_id(normalized_state, catalog, action_id) in (
            normalized_state.legal_actions
        )


def test_mission3_terminal_state_has_empty_legal_action_ids_and_all_false_mask() -> None:
    mission = load_mission(MISSION_PATH)
    catalog = build_mission3_action_catalog(mission)
    base_state = create_initial_game_state(mission, seed=0)
    terminal_like_state = replace(
        base_state,
        phase=GamePhase.GERMAN,
        activated_british_unit_ids=frozenset(base_state.british_units),
        activated_german_unit_ids=frozenset(),
        pending_decision=ChooseGermanUnitContext(),
        current_activation=None,
        unresolved_markers={},
        german_units={
            "qm_1": RevealedGermanUnitState(
                unit_id="qm_1",
                unit_class="light_machine_gun",
                position=HexCoord(-1, 2),
                facing=HexDirection.DOWN,
                status=GermanUnitStatus.REMOVED,
            ),
        },
    )

    normalized_state = normalize_env_state(terminal_like_state)
    selection = build_legal_action_selection(normalized_state, catalog)

    assert normalized_state.legal_actions == ()
    assert selection.legal_action_ids == ()
    assert selection.legal_action_mask == (False,) * catalog.size


def test_mission3_decode_legal_action_id_rejects_in_range_but_currently_illegal_ids() -> None:
    mission = load_mission(MISSION_PATH)
    catalog = build_mission3_action_catalog(mission)
    normalized_state = normalize_env_state(_initial_state())
    order_execution_action_id = catalog.encode(
        ChooseOrderExecutionAction(choice=OrderExecutionChoice.FIRST_ORDER_ONLY),
    )

    with pytest.raises(IllegalActionIdError, match="illegal in the current state"):
        decode_legal_action_id(normalized_state, catalog, order_execution_action_id)
