from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from solo_wargame_ai.domain.actions import (
    ChooseOrderExecutionAction,
    OrderExecutionChoice,
)
from solo_wargame_ai.domain.decision_context import (
    ChooseOrderExecutionContext,
    ChooseOrderParameterContext,
    DecisionContextKind,
)
from solo_wargame_ai.domain.legal_actions import apply_action, get_legal_actions
from solo_wargame_ai.domain.mission import OrderName
from solo_wargame_ai.domain.state import CurrentActivation, create_initial_game_state
from solo_wargame_ai.domain.units import BritishMorale
from solo_wargame_ai.io.mission_loader import load_mission

MISSION_PATH = (
    Path(__file__).resolve().parents[1]
    / "configs"
    / "missions"
    / "mission_01_secure_the_woods_1.toml"
)


def test_low_morale_legal_actions_exclude_second_only_and_both_orders() -> None:
    state = _state_at_low_morale_order_execution()

    assert state.pending_decision.kind is DecisionContextKind.CHOOSE_ORDER_EXECUTION
    assert get_legal_actions(state) == (
        ChooseOrderExecutionAction(choice=OrderExecutionChoice.FIRST_ORDER_ONLY),
        ChooseOrderExecutionAction(choice=OrderExecutionChoice.NO_ACTION),
    )


def test_low_morale_first_order_only_remains_legal_and_stages_first_order() -> None:
    state = _state_at_low_morale_order_execution()

    next_state = apply_action(
        state,
        ChooseOrderExecutionAction(choice=OrderExecutionChoice.FIRST_ORDER_ONLY),
    )

    assert isinstance(next_state.pending_decision, ChooseOrderParameterContext)
    assert next_state.pending_decision.order is OrderName.RALLY
    assert next_state.pending_decision.order_index == 0
    assert next_state.current_activation is not None
    assert next_state.current_activation.planned_orders == (OrderName.RALLY,)
    assert next_state.current_activation.next_order_index == 0


def test_low_morale_no_action_remains_legal_and_ends_activation() -> None:
    state = _state_at_low_morale_order_execution()

    next_state = apply_action(
        state,
        ChooseOrderExecutionAction(choice=OrderExecutionChoice.NO_ACTION),
    )

    assert next_state.current_activation is None
    assert next_state.pending_decision.kind is DecisionContextKind.CHOOSE_BRITISH_UNIT
    assert next_state.activated_british_unit_ids == frozenset({"rifle_squad_a"})


def _state_at_low_morale_order_execution():
    mission = load_mission(MISSION_PATH)
    state = create_initial_game_state(mission)
    low_morale_unit = replace(
        state.british_units["rifle_squad_a"],
        morale=BritishMorale.LOW,
    )
    return replace(
        state,
        british_units={**state.british_units, "rifle_squad_a": low_morale_unit},
        pending_decision=ChooseOrderExecutionContext(),
        current_activation=CurrentActivation(
            active_unit_id="rifle_squad_a",
            roll=(1, 2),
            selected_die=1,
        ),
    )
