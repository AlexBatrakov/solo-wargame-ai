from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from solo_wargame_ai.domain.actions import ChooseOrderExecutionAction, OrderExecutionChoice
from solo_wargame_ai.domain.decision_context import (
    ChooseOrderExecutionContext,
    ChooseOrderParameterContext,
)
from solo_wargame_ai.domain.legal_actions import apply_action, lookup_orders_chart_row
from solo_wargame_ai.domain.mission import OrderName
from solo_wargame_ai.domain.state import CurrentActivation, create_initial_game_state
from solo_wargame_ai.io.mission_loader import load_mission

MISSION_PATH = (
    Path(__file__).resolve().parents[1]
    / "configs"
    / "missions"
    / "mission_01_secure_the_woods_1.toml"
)


@pytest.mark.parametrize(
    ("die_value", "expected_orders"),
    [
        (1, (OrderName.RALLY, OrderName.GRENADE_ATTACK)),
        (2, (OrderName.ADVANCE, OrderName.SCOUT)),
        (3, (OrderName.ADVANCE, OrderName.TAKE_COVER)),
        (4, (OrderName.FIRE, OrderName.TAKE_COVER)),
        (5, (OrderName.FIRE, OrderName.ADVANCE)),
        (6, (OrderName.ADVANCE, OrderName.FIRE)),
    ],
)
def test_lookup_orders_chart_row_returns_rifle_squad_row_for_each_die_value(
    die_value: int,
    expected_orders: tuple[OrderName, OrderName],
) -> None:
    mission = load_mission(MISSION_PATH)

    row = lookup_orders_chart_row(
        mission,
        unit_class="rifle_squad",
        die_value=die_value,
    )

    assert row.orders == expected_orders


@pytest.mark.parametrize(
    ("choice", "expected_orders"),
    [
        (OrderExecutionChoice.FIRST_ORDER_ONLY, (OrderName.ADVANCE,)),
        (OrderExecutionChoice.SECOND_ORDER_ONLY, (OrderName.FIRE,)),
        (OrderExecutionChoice.BOTH_ORDERS, (OrderName.ADVANCE, OrderName.FIRE)),
    ],
)
def test_choose_order_execution_populates_planned_orders_for_requested_choice(
    choice: OrderExecutionChoice,
    expected_orders: tuple[OrderName, ...],
) -> None:
    state = _state_at_choose_order_execution(selected_die=6)

    next_state = apply_action(
        state,
        ChooseOrderExecutionAction(choice=choice),
    )

    assert isinstance(next_state.pending_decision, ChooseOrderParameterContext)
    assert next_state.pending_decision.order is expected_orders[0]
    assert next_state.pending_decision.order_index == 0
    assert next_state.current_activation is not None
    assert next_state.current_activation.planned_orders == expected_orders
    assert next_state.current_activation.next_order_index == 0


def test_choose_order_execution_no_action_ends_activation_immediately() -> None:
    state = _state_at_choose_order_execution(selected_die=6)

    next_state = apply_action(
        state,
        ChooseOrderExecutionAction(choice=OrderExecutionChoice.NO_ACTION),
    )

    assert next_state.current_activation is None
    assert next_state.activated_british_unit_ids == frozenset({"rifle_squad_a"})
    assert next_state.pending_decision.kind.value == "choose_british_unit"


def _state_at_choose_order_execution(*, selected_die: int):
    mission = load_mission(MISSION_PATH)
    initial_state = create_initial_game_state(mission)
    return replace(
        initial_state,
        pending_decision=ChooseOrderExecutionContext(),
        current_activation=CurrentActivation(
            active_unit_id="rifle_squad_a",
            roll=(selected_die, 1),
            selected_die=selected_die,
        ),
    )
