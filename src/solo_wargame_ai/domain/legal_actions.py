"""Stage 4 legality and staged British activation transitions."""

from __future__ import annotations

from dataclasses import replace

from .actions import (
    ChooseOrderExecutionAction,
    DiscardActivationRollAction,
    DoubleChoiceOption,
    GameAction,
    OrderExecutionChoice,
    ResolveDoubleChoiceAction,
    SelectActivationDieAction,
    SelectBritishUnitAction,
    SelectGermanUnitAction,
)
from .decision_context import (
    ChooseActivationDieContext,
    ChooseBritishUnitContext,
    ChooseDoubleChoiceContext,
    ChooseGermanUnitContext,
    ChooseOrderExecutionContext,
    ChooseOrderParameterContext,
    DecisionContextKind,
)
from .mission import Mission, OrderName, OrdersChartRow
from .rng import DeterministicRNG
from .state import CurrentActivation, GamePhase, GameState, validate_game_state
from .units import BritishMorale, GermanUnitStatus


class IllegalActionError(ValueError):
    """Raised when a caller tries to apply an action that is illegal in the state."""


def get_legal_actions(state: GameState) -> tuple[GameAction, ...]:
    """Return all legal actions for the state's current pending decision."""

    validate_game_state(state)

    pending_kind = state.pending_decision.kind

    if pending_kind is DecisionContextKind.CHOOSE_BRITISH_UNIT:
        return tuple(
            SelectBritishUnitAction(unit_id=unit_id)
            for unit_id in _selectable_british_unit_ids(
                state,
                activated_british_unit_ids=state.activated_british_unit_ids,
            )
        )

    if pending_kind is DecisionContextKind.CHOOSE_DOUBLE_CHOICE:
        return (
            ResolveDoubleChoiceAction(choice=DoubleChoiceOption.KEEP),
            ResolveDoubleChoiceAction(choice=DoubleChoiceOption.REROLL),
        )

    if pending_kind is DecisionContextKind.CHOOSE_ACTIVATION_DIE:
        activation = _require_current_activation(state)
        die_actions: list[GameAction] = []
        seen_die_values: set[int] = set()
        for die_value in activation.roll or ():
            if die_value in seen_die_values:
                continue
            seen_die_values.add(die_value)
            die_actions.append(SelectActivationDieAction(die_value=die_value))
        die_actions.append(DiscardActivationRollAction())
        return tuple(die_actions)

    if pending_kind is DecisionContextKind.CHOOSE_ORDER_EXECUTION:
        return tuple(
            ChooseOrderExecutionAction(choice=choice)
            for choice in _legal_order_execution_choices(state)
        )

    if pending_kind is DecisionContextKind.CHOOSE_GERMAN_UNIT:
        return tuple(
            SelectGermanUnitAction(unit_id=unit_id)
            for unit_id in _selectable_german_unit_ids(state)
        )

    if pending_kind is DecisionContextKind.CHOOSE_ORDER_PARAMETER:
        return ()

    raise AssertionError(f"Unhandled pending decision kind: {pending_kind!r}")


def apply_action(state: GameState, action: GameAction) -> GameState:
    """Apply one legal Stage 4 action and return the resulting state."""

    legal_actions = get_legal_actions(state)
    if action not in legal_actions:
        raise IllegalActionError(
            "Illegal action for pending decision "
            f"{state.pending_decision.kind.value}: {action!r}",
        )

    if isinstance(action, SelectBritishUnitAction):
        return _apply_select_british_unit_action(state, action)

    if isinstance(action, ResolveDoubleChoiceAction):
        return _apply_resolve_double_choice_action(state, action)

    if isinstance(action, SelectActivationDieAction):
        return _apply_select_activation_die_action(state, action)

    if isinstance(action, DiscardActivationRollAction):
        return _finish_british_activation(state)

    if isinstance(action, ChooseOrderExecutionAction):
        return _apply_choose_order_execution_action(state, action)

    if isinstance(action, SelectGermanUnitAction):
        raise NotImplementedError("German activation resolution is out of scope for Stage 4")

    raise IllegalActionError(f"Stage 4 does not support applying action {action!r}")


def lookup_orders_chart_row(
    mission: Mission,
    *,
    unit_class: str,
    die_value: int,
) -> OrdersChartRow:
    """Look up the Mission Orders Chart row for the selected unit class and die."""

    chart = mission.british.orders_charts_by_unit_class.get(unit_class)
    if chart is None:
        raise ValueError(f"Mission has no Orders Chart for British unit class {unit_class!r}")

    row = chart.rows_by_die_value.get(die_value)
    if row is None:
        raise ValueError(
            "Mission Orders Chart has no row for British unit class "
            f"{unit_class!r} and die value {die_value}",
        )
    return row


def _selectable_british_unit_ids(
    state: GameState,
    *,
    activated_british_unit_ids: frozenset[str],
) -> tuple[str, ...]:
    selectable_unit_ids: list[str] = []
    for unit_id, unit_state in state.british_units.items():
        if unit_state.morale is BritishMorale.REMOVED:
            continue
        if unit_id in activated_british_unit_ids:
            continue
        selectable_unit_ids.append(unit_id)
    return tuple(selectable_unit_ids)


def _selectable_german_unit_ids(state: GameState) -> tuple[str, ...]:
    selectable_unit_ids: list[str] = []
    for unit_id, unit_state in state.german_units.items():
        if unit_state.status is GermanUnitStatus.REMOVED:
            continue
        if unit_id in state.activated_german_unit_ids:
            continue
        selectable_unit_ids.append(unit_id)
    return tuple(selectable_unit_ids)


def _legal_order_execution_choices(state: GameState) -> tuple[OrderExecutionChoice, ...]:
    activation = _require_current_activation(state)
    active_unit = state.british_units[activation.active_unit_id]

    if active_unit.morale is BritishMorale.LOW:
        return (
            OrderExecutionChoice.FIRST_ORDER_ONLY,
            OrderExecutionChoice.NO_ACTION,
        )

    return (
        OrderExecutionChoice.FIRST_ORDER_ONLY,
        OrderExecutionChoice.SECOND_ORDER_ONLY,
        OrderExecutionChoice.BOTH_ORDERS,
        OrderExecutionChoice.NO_ACTION,
    )


def _apply_select_british_unit_action(
    state: GameState,
    action: SelectBritishUnitAction,
) -> GameState:
    rng = DeterministicRNG.from_state(state.rng_state)
    roll = rng.roll_nd6(2)
    pending_decision = (
        ChooseDoubleChoiceContext() if _is_double_roll(roll) else ChooseActivationDieContext()
    )

    next_state = replace(
        state,
        pending_decision=pending_decision,
        current_activation=CurrentActivation(
            active_unit_id=action.unit_id,
            roll=roll,
        ),
        rng_state=rng.snapshot(),
    )
    validate_game_state(next_state)
    return next_state


def _apply_resolve_double_choice_action(
    state: GameState,
    action: ResolveDoubleChoiceAction,
) -> GameState:
    activation = _require_current_activation(state)

    if action.choice is DoubleChoiceOption.KEEP:
        next_state = replace(
            state,
            pending_decision=ChooseActivationDieContext(),
        )
        validate_game_state(next_state)
        return next_state

    rng = DeterministicRNG.from_state(state.rng_state)
    roll = rng.roll_nd6(2)
    pending_decision = (
        ChooseDoubleChoiceContext() if _is_double_roll(roll) else ChooseActivationDieContext()
    )

    next_state = replace(
        state,
        pending_decision=pending_decision,
        current_activation=replace(
            activation,
            roll=roll,
            selected_die=None,
            planned_orders=(),
            next_order_index=0,
        ),
        rng_state=rng.snapshot(),
    )
    validate_game_state(next_state)
    return next_state


def _apply_select_activation_die_action(
    state: GameState,
    action: SelectActivationDieAction,
) -> GameState:
    activation = _require_current_activation(state)
    next_state = replace(
        state,
        pending_decision=ChooseOrderExecutionContext(),
        current_activation=replace(activation, selected_die=action.die_value),
    )
    validate_game_state(next_state)
    return next_state


def _apply_choose_order_execution_action(
    state: GameState,
    action: ChooseOrderExecutionAction,
) -> GameState:
    activation = _require_current_activation(state)
    active_unit = state.british_units[activation.active_unit_id]
    orders_row = lookup_orders_chart_row(
        state.mission,
        unit_class=active_unit.unit_class,
        die_value=activation.selected_die or 0,
    )

    if action.choice is OrderExecutionChoice.NO_ACTION:
        return _finish_british_activation(state)

    planned_orders = _planned_orders_for_choice(orders_row, action.choice)
    next_state = replace(
        state,
        pending_decision=ChooseOrderParameterContext(
            order=planned_orders[0],
            order_index=0,
        ),
        current_activation=replace(
            activation,
            planned_orders=planned_orders,
            next_order_index=0,
        ),
    )
    validate_game_state(next_state)
    return next_state


def _planned_orders_for_choice(
    orders_row: OrdersChartRow,
    choice: OrderExecutionChoice,
) -> tuple[OrderName, ...]:
    if choice is OrderExecutionChoice.FIRST_ORDER_ONLY:
        return (orders_row.first_order,)
    if choice is OrderExecutionChoice.SECOND_ORDER_ONLY:
        return (orders_row.second_order,)
    if choice is OrderExecutionChoice.BOTH_ORDERS:
        return (orders_row.first_order, orders_row.second_order)
    raise IllegalActionError(f"Cannot build planned orders for choice {choice!r}")


def _finish_british_activation(state: GameState) -> GameState:
    activation = _require_current_activation(state)
    activated_unit_ids = frozenset(
        (*state.activated_british_unit_ids, activation.active_unit_id),
    )
    remaining_british_units = _selectable_british_unit_ids(
        state,
        activated_british_unit_ids=activated_unit_ids,
    )

    if remaining_british_units:
        next_state = replace(
            state,
            activated_british_unit_ids=activated_unit_ids,
            pending_decision=ChooseBritishUnitContext(),
            current_activation=None,
        )
        validate_game_state(next_state)
        return next_state

    next_state = replace(
        state,
        phase=GamePhase.GERMAN,
        activated_british_unit_ids=activated_unit_ids,
        activated_german_unit_ids=frozenset(),
        pending_decision=ChooseGermanUnitContext(),
        current_activation=None,
    )
    validate_game_state(next_state)
    return next_state


def _require_current_activation(state: GameState) -> CurrentActivation:
    activation = state.current_activation
    if activation is None:
        raise AssertionError("Stage 4 requires current_activation for this pending decision")
    return activation


def _is_double_roll(roll: tuple[int, int]) -> bool:
    return roll[0] == roll[1]


__all__ = [
    "IllegalActionError",
    "apply_action",
    "get_legal_actions",
    "lookup_orders_chart_row",
]
