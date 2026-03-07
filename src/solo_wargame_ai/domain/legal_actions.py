"""Stage 4/5/6A legality and staged British activation transitions."""

from __future__ import annotations

from dataclasses import replace

from .actions import (
    AdvanceAction,
    ChooseOrderExecutionAction,
    DiscardActivationRollAction,
    DoubleChoiceOption,
    FireAction,
    GameAction,
    GrenadeAttackAction,
    OrderExecutionChoice,
    RallyAction,
    ResolveDoubleChoiceAction,
    ScoutAction,
    SelectActivationDieAction,
    SelectBritishUnitAction,
    SelectGermanUnitAction,
    TakeCoverAction,
)
from .combat import resolve_british_attack
from .decision_context import (
    ChooseActivationDieContext,
    ChooseBritishUnitContext,
    ChooseDoubleChoiceContext,
    ChooseGermanUnitContext,
    ChooseOrderExecutionContext,
    ChooseOrderParameterContext,
    DecisionContextKind,
)
from .hexgrid import HexCoord, are_adjacent, british_forward_neighbors
from .mission import Mission, OrderName, OrdersChartRow
from .reveal import legal_scout_facing_directions, reveal_by_movement, reveal_by_scout
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
        return _legal_order_parameter_actions(state)

    raise AssertionError(f"Unhandled pending decision kind: {pending_kind!r}")


def apply_action(state: GameState, action: GameAction) -> GameState:
    """Apply one legal Stage 4/5/6A action and return the resulting state."""

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

    if isinstance(action, AdvanceAction):
        return _apply_advance_action(state, action)

    if isinstance(action, FireAction):
        return _apply_british_attack_action(
            state,
            attack_order=OrderName.FIRE,
            target_unit_id=action.target_unit_id,
        )

    if isinstance(action, GrenadeAttackAction):
        return _apply_british_attack_action(
            state,
            attack_order=OrderName.GRENADE_ATTACK,
            target_unit_id=action.target_unit_id,
        )

    if isinstance(action, TakeCoverAction):
        return _apply_take_cover_action(state)

    if isinstance(action, RallyAction):
        return _apply_rally_action(state)

    if isinstance(action, ScoutAction):
        return _apply_scout_action(state, action)

    if isinstance(action, SelectGermanUnitAction):
        raise NotImplementedError("German activation resolution is out of scope for Stage 5")

    raise IllegalActionError(f"Stage 5 does not support applying action {action!r}")


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


def _legal_order_parameter_actions(state: GameState) -> tuple[GameAction, ...]:
    activation = _require_current_activation(state)
    context = _require_order_parameter_context(state)
    if activation.active_order is not context.order:
        raise AssertionError("pending order parameter does not match the active staged order")

    active_unit = state.british_units[activation.active_unit_id]

    if context.order is OrderName.ADVANCE:
        return tuple(
            AdvanceAction(destination=destination)
            for destination in _legal_advance_destinations(state, active_unit.position)
        )

    if context.order is OrderName.FIRE:
        return tuple(
            FireAction(target_unit_id=unit_id)
            for unit_id in _legal_attack_target_ids(state, active_unit.position)
        )

    if context.order is OrderName.GRENADE_ATTACK:
        return tuple(
            GrenadeAttackAction(target_unit_id=unit_id)
            for unit_id in _legal_attack_target_ids(state, active_unit.position)
        )

    if context.order is OrderName.TAKE_COVER:
        return (TakeCoverAction(),)

    if context.order is OrderName.RALLY:
        return (RallyAction(),)

    if context.order is OrderName.SCOUT:
        return _legal_scout_actions(state, active_unit.position)

    return ()


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


def _apply_advance_action(state: GameState, action: AdvanceAction) -> GameState:
    activation = _require_current_activation(state)
    active_unit = state.british_units[activation.active_unit_id]
    updated_active_unit = replace(active_unit, position=action.destination, cover=0)
    british_units = dict(state.british_units)
    british_units[active_unit.unit_id] = updated_active_unit

    rng = DeterministicRNG.from_state(state.rng_state)
    reveal_resolution = reveal_by_movement(state, destination=action.destination, rng=rng)
    rng_state = rng.snapshot() if reveal_resolution.revealed_marker_ids else state.rng_state

    return _continue_after_resolved_order(
        state,
        british_units=british_units,
        german_units=reveal_resolution.german_units,
        unresolved_markers=reveal_resolution.unresolved_markers,
        rng_state=rng_state,
    )


def _apply_take_cover_action(state: GameState) -> GameState:
    activation = _require_current_activation(state)
    active_unit = state.british_units[activation.active_unit_id]
    british_units = dict(state.british_units)
    british_units[active_unit.unit_id] = replace(active_unit, cover=active_unit.cover + 1)
    return _continue_after_resolved_order(
        state,
        british_units=british_units,
        german_units=state.german_units,
        unresolved_markers=state.unresolved_markers,
        rng_state=state.rng_state,
    )


def _apply_rally_action(state: GameState) -> GameState:
    activation = _require_current_activation(state)
    active_unit = state.british_units[activation.active_unit_id]
    updated_morale = (
        BritishMorale.NORMAL if active_unit.morale is BritishMorale.LOW else active_unit.morale
    )
    british_units = dict(state.british_units)
    british_units[active_unit.unit_id] = replace(active_unit, morale=updated_morale)
    return _continue_after_resolved_order(
        state,
        british_units=british_units,
        german_units=state.german_units,
        unresolved_markers=state.unresolved_markers,
        rng_state=state.rng_state,
    )


def _apply_scout_action(state: GameState, action: ScoutAction) -> GameState:
    if action.facing is None:
        raise AssertionError("ScoutAction requires a facing when resolved by Stage 5")

    rng = DeterministicRNG.from_state(state.rng_state)
    reveal_resolution = reveal_by_scout(
        state,
        marker_id=action.marker_id,
        facing=action.facing,
        rng=rng,
    )
    return _continue_after_resolved_order(
        state,
        british_units=state.british_units,
        german_units=reveal_resolution.german_units,
        unresolved_markers=reveal_resolution.unresolved_markers,
        rng_state=rng.snapshot(),
    )


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


def _apply_british_attack_action(
    state: GameState,
    *,
    attack_order: OrderName,
    target_unit_id: str,
) -> GameState:
    attack_outcome = resolve_british_attack(
        state,
        attack_order=attack_order,
        target_unit_id=target_unit_id,
    )
    return _continue_after_resolved_order(
        state,
        british_units=state.british_units,
        german_units=attack_outcome.german_units,
        unresolved_markers=state.unresolved_markers,
        rng_state=attack_outcome.rng_state,
    )


def _continue_after_resolved_order(
    state: GameState,
    *,
    british_units,
    german_units,
    unresolved_markers,
    rng_state,
) -> GameState:
    activation = _require_current_activation(state)
    next_order_index = activation.next_order_index + 1

    if next_order_index < len(activation.planned_orders):
        next_order = activation.planned_orders[next_order_index]
        next_state = replace(
            state,
            british_units=british_units,
            german_units=german_units,
            unresolved_markers=unresolved_markers,
            pending_decision=ChooseOrderParameterContext(
                order=next_order,
                order_index=next_order_index,
            ),
            current_activation=replace(
                activation,
                next_order_index=next_order_index,
            ),
            rng_state=rng_state,
        )
        validate_game_state(next_state)
        return next_state

    completed_state = replace(
        state,
        british_units=british_units,
        german_units=german_units,
        unresolved_markers=unresolved_markers,
        rng_state=rng_state,
    )
    return _finish_british_activation(completed_state)


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


def _legal_advance_destinations(state: GameState, position: HexCoord) -> tuple[HexCoord, ...]:
    occupied_by_german = {
        unit.position
        for unit in state.german_units.values()
        if unit.status is GermanUnitStatus.ACTIVE
    }
    return tuple(
        destination
        for destination in british_forward_neighbors(
            position,
            forward_directions=state.mission.map.forward_directions,
        )
        if state.mission.map.is_playable_hex(destination) and destination not in occupied_by_german
    )


def _legal_attack_target_ids(state: GameState, attacker_position: HexCoord) -> tuple[str, ...]:
    return tuple(
        unit_id
        for unit_id, unit_state in state.german_units.items()
        if unit_state.status is GermanUnitStatus.ACTIVE
        and are_adjacent(attacker_position, unit_state.position)
    )


def _legal_scout_actions(state: GameState, unit_position: HexCoord) -> tuple[ScoutAction, ...]:
    actions: list[ScoutAction] = []
    for marker in state.mission.map.hidden_markers:
        marker_state = state.unresolved_markers.get(marker.marker_id)
        if marker_state is None:
            continue
        if _hex_distance(unit_position, marker_state.position) != 2:
            continue
        for facing in legal_scout_facing_directions(state.mission, marker_state.position):
            actions.append(ScoutAction(marker_id=marker_state.marker_id, facing=facing))
    return tuple(actions)


def _require_order_parameter_context(state: GameState) -> ChooseOrderParameterContext:
    context = state.pending_decision
    if not isinstance(context, ChooseOrderParameterContext):
        raise AssertionError("Stage 5 expected ChooseOrderParameterContext")
    return context


def _require_current_activation(state: GameState) -> CurrentActivation:
    activation = state.current_activation
    if activation is None:
        raise AssertionError("Stage 4/5 requires current_activation for this pending decision")
    return activation


def _is_double_roll(roll: tuple[int, int]) -> bool:
    return roll[0] == roll[1]


def _hex_distance(first: HexCoord, second: HexCoord) -> int:
    delta_q = second.q - first.q
    delta_r = second.r - first.r
    return max(abs(delta_q), abs(delta_r), abs(delta_q + delta_r))


__all__ = [
    "IllegalActionError",
    "apply_action",
    "get_legal_actions",
    "lookup_orders_chart_row",
]
