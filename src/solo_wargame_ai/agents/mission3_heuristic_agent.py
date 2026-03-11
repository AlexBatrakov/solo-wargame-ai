"""Mission 3-local heuristic baseline for the active baseline/search packet."""

from __future__ import annotations

from dataclasses import replace

from solo_wargame_ai.domain.actions import (
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
from solo_wargame_ai.domain.combat import (
    calculate_fire_threshold,
    calculate_grenade_attack_threshold,
    german_fire_zone_hexes,
)
from solo_wargame_ai.domain.decision_context import ChooseOrderExecutionContext
from solo_wargame_ai.domain.hexgrid import HexCoord, are_adjacent, british_forward_neighbors
from solo_wargame_ai.domain.mission import Mission
from solo_wargame_ai.domain.resolver import apply_action, get_legal_actions
from solo_wargame_ai.domain.state import CurrentActivation, GameState, TerminalOutcome
from solo_wargame_ai.domain.terrain import TerrainType
from solo_wargame_ai.domain.units import (
    BritishMorale,
    BritishUnitState,
    GermanUnitStatus,
    RevealedGermanUnitState,
)


def evaluate_mission3_state(state: GameState) -> float:
    """Return a Mission 3-local frontier value for non-learning comparisons."""

    if state.terminal_outcome is TerminalOutcome.VICTORY:
        return 10_000.0 - (50.0 * state.turn)
    if state.terminal_outcome is TerminalOutcome.DEFEAT:
        return -10_000.0 + (40.0 * _removed_german_count(state))

    active_german_count = sum(
        1
        for german_unit in state.german_units.values()
        if german_unit.status is GermanUnitStatus.ACTIVE
    )
    unresolved_marker_count = len(state.unresolved_markers)
    removed_british_count = sum(
        1
        for unit in state.british_units.values()
        if unit.morale is BritishMorale.REMOVED
    )
    low_morale_count = sum(
        1
        for unit in state.british_units.values()
        if unit.morale is BritishMorale.LOW
    )
    living_british_units = tuple(
        unit
        for unit in state.british_units.values()
        if unit.morale is not BritishMorale.REMOVED
    )

    distance_score = sum(
        _distance_to_objective(unit.position, state)
        for unit in living_british_units
    )
    fire_zone_penalty = sum(
        _active_fire_zone_count(unit.position, state)
        for unit in living_british_units
    )
    terrain_score = sum(
        _terrain_bonus(unit.position, state.mission)
        for unit in living_british_units
    )
    cover_score = sum(min(unit.cover, 2) for unit in living_british_units)
    attack_ready_count = sum(
        1
        for unit in living_british_units
        if any(
            german_unit.status is GermanUnitStatus.ACTIVE
            and are_adjacent(unit.position, german_unit.position)
            for german_unit in state.german_units.values()
        )
    )

    return (
        -(110.0 * active_german_count)
        -(95.0 * unresolved_marker_count)
        -(180.0 * removed_british_count)
        -(75.0 * low_morale_count)
        -(9.0 * distance_score)
        -(16.0 * fire_zone_penalty)
        +(40.0 * _removed_german_count(state))
        +(18.0 * attack_ready_count)
        +(6.0 * terrain_score)
        +(4.0 * cover_score)
        -(22.0 * (state.turn - 1))
    )


class Mission3HeuristicAgent:
    """Prefer marker revelation, favorable attacks, and safer Mission 3 progress."""

    name = "heuristic"

    def __init__(self, *, lookahead_depth: int = 2) -> None:
        self._lookahead_depth = lookahead_depth

    def select_action(
        self,
        state: GameState,
        legal_actions: tuple[GameAction, ...],
    ) -> GameAction:
        if not legal_actions:
            raise ValueError("Mission3HeuristicAgent requires at least one legal action")

        return min(
            legal_actions,
            key=lambda action: (
                -self._score_action(state, action, depth=self._lookahead_depth),
                _tie_break_key(action),
            ),
        )

    def _score_action(
        self,
        state: GameState,
        action: GameAction,
        *,
        depth: int,
    ) -> float:
        if depth <= 0:
            return self._shallow_action_score(state, action)

        score = self._base_action_score(state, action)

        if isinstance(action, ResolveDoubleChoiceAction):
            if action.choice is DoubleChoiceOption.REROLL:
                return score + self._expected_activation_value_for_current_unit(state)
            return score + self._lookahead_score(state, action, depth=depth + 1)

        if isinstance(
            action,
            SelectBritishUnitAction
            | SelectActivationDieAction
            | ChooseOrderExecutionAction
            | DiscardActivationRollAction,
        ):
            return score + self._lookahead_score(state, action, depth=depth)

        next_state = apply_action(state, action)
        return score + (0.2 * evaluate_mission3_state(next_state))

    def _shallow_action_score(self, state: GameState, action: GameAction) -> float:
        if isinstance(action, SelectBritishUnitAction):
            return self._unit_priority_score(state, action.unit_id)
        if isinstance(action, ResolveDoubleChoiceAction):
            return 0.0
        if isinstance(action, SelectActivationDieAction):
            return 0.0
        if isinstance(action, DiscardActivationRollAction):
            return -18.0
        return self._base_action_score(state, action)

    def _lookahead_score(
        self,
        state: GameState,
        action: GameAction,
        *,
        depth: int,
    ) -> float:
        next_state = apply_action(state, action)
        if next_state.terminal_outcome is not None:
            return evaluate_mission3_state(next_state)

        next_legal_actions = get_legal_actions(next_state)
        if not next_legal_actions:
            return evaluate_mission3_state(next_state)

        return max(
            self._score_action(next_state, next_action, depth=depth - 1)
            for next_action in next_legal_actions
        )

    def _base_action_score(self, state: GameState, action: GameAction) -> float:
        if isinstance(action, SelectBritishUnitAction):
            return self._expected_activation_value(state, action.unit_id)
        if isinstance(action, ResolveDoubleChoiceAction):
            return 0.0
        if isinstance(action, SelectActivationDieAction):
            return 0.0
        if isinstance(action, DiscardActivationRollAction):
            return -18.0
        if isinstance(action, ChooseOrderExecutionAction):
            return {
                OrderExecutionChoice.NO_ACTION: -40.0,
                OrderExecutionChoice.FIRST_ORDER_ONLY: 2.0,
                OrderExecutionChoice.SECOND_ORDER_ONLY: -4.0,
                OrderExecutionChoice.BOTH_ORDERS: 10.0,
            }[action.choice]
        if isinstance(action, AdvanceAction):
            return self._advance_score(state, action)
        if isinstance(action, FireAction):
            return self._attack_score(state, action)
        if isinstance(action, GrenadeAttackAction):
            return self._attack_score(state, action)
        if isinstance(action, TakeCoverAction):
            return self._take_cover_score(state)
        if isinstance(action, RallyAction):
            return self._rally_score(state)
        if isinstance(action, ScoutAction):
            return self._scout_score(state, action)
        if isinstance(action, SelectGermanUnitAction):
            next_state = apply_action(state, action)
            return evaluate_mission3_state(next_state)
        raise AssertionError(f"Unsupported action type: {type(action)!r}")

    def _expected_activation_value_for_current_unit(self, state: GameState) -> float:
        if state.current_activation is None:
            raise AssertionError("current activation is required to evaluate rerolls")
        return self._expected_activation_value(state, state.current_activation.active_unit_id)

    def _expected_activation_value(self, state: GameState, unit_id: str) -> float:
        total = 0.0
        for die_value in range(1, 7):
            synthetic_state = self._synthetic_order_execution_state(
                state,
                unit_id=unit_id,
                die_value=die_value,
            )
            legal_actions = get_legal_actions(synthetic_state)
            if not legal_actions:
                continue
            total += max(
                self._base_action_score(synthetic_state, action)
                for action in legal_actions
            )
        return total / 6.0

    def _unit_priority_score(self, state: GameState, unit_id: str) -> float:
        unit = state.british_units[unit_id]
        score = 28.0 - (4.0 * _distance_to_objective(unit.position, state))
        score += 20.0 * self._best_reveal_count(unit.position, state)
        if unit.morale is BritishMorale.LOW:
            score += 24.0
        if _is_adjacent_to_active_german(unit.position, state):
            score += 18.0
        return score

    def _synthetic_order_execution_state(
        self,
        state: GameState,
        *,
        unit_id: str,
        die_value: int,
    ) -> GameState:
        return replace(
            state,
            pending_decision=ChooseOrderExecutionContext(),
            current_activation=CurrentActivation(
                active_unit_id=unit_id,
                roll=(die_value, die_value),
                selected_die=die_value,
            ),
        )

    def _advance_score(self, state: GameState, action: AdvanceAction) -> float:
        active_unit = self._active_unit(state)
        current_position = active_unit.position
        destination = action.destination
        reveal_count = _revealed_marker_count(destination, state)

        score = 60.0
        score += 14.0 * (
            _distance_to_objective(current_position, state)
            - _distance_to_objective(destination, state)
        )
        score += 38.0 * reveal_count
        if reveal_count > 1:
            score += 18.0
        if _is_adjacent_to_active_german(destination, state):
            score += 20.0
        score += 6.0 * _terrain_bonus(destination, state.mission)
        score -= 10.0 * _active_fire_zone_count(destination, state)
        if active_unit.morale is BritishMorale.LOW:
            score -= 12.0
        return score

    def _attack_score(
        self,
        state: GameState,
        action: FireAction | GrenadeAttackAction,
    ) -> float:
        active_unit = self._active_unit(state)
        target = state.german_units[action.target_unit_id]
        if isinstance(action, FireAction):
            threshold = calculate_fire_threshold(
                state.mission,
                attacker=active_unit,
                defender=target,
                british_units=state.british_units,
            )
        else:
            threshold = calculate_grenade_attack_threshold(
                state.mission,
                attacker=active_unit,
            )
        target_hex_bonus = _terrain_bonus(target.position, state.mission)
        return 120.0 + (110.0 * _two_d6_hit_probability(threshold)) - (8.0 * target_hex_bonus)

    def _take_cover_score(self, state: GameState) -> float:
        active_unit = self._active_unit(state)
        threat_count = _active_fire_zone_count(active_unit.position, state)
        return 22.0 + (20.0 * threat_count) - (6.0 * active_unit.cover)

    def _rally_score(self, state: GameState) -> float:
        active_unit = self._active_unit(state)
        if active_unit.morale is BritishMorale.LOW:
            return 110.0
        return -12.0

    def _scout_score(self, state: GameState, action: ScoutAction) -> float:
        marker = state.unresolved_markers[action.marker_id]
        exposed_british_units = sum(
            1
            for unit in state.british_units.values()
            if unit.morale is not BritishMorale.REMOVED
            and action.facing is not None
            and unit.position in _hypothetical_fire_zone_hexes(
                state.mission,
                marker.position,
                action.facing,
            )
        )
        return 78.0 - (18.0 * exposed_british_units)

    def _best_reveal_count(self, position: HexCoord, state: GameState) -> int:
        forward_destinations = tuple(
            destination
            for destination in british_forward_neighbors(
                position,
                forward_directions=state.mission.map.forward_directions,
            )
            if state.mission.map.is_playable_hex(destination)
        )
        if not forward_destinations:
            return 0
        return max(
            _revealed_marker_count(destination, state)
            for destination in forward_destinations
        )

    def _active_unit(self, state: GameState) -> BritishUnitState:
        if state.current_activation is None:
            raise AssertionError("current activation is required to score this action")
        return state.british_units[state.current_activation.active_unit_id]


def _distance_to_objective(coord: HexCoord, state: GameState) -> int:
    targets = tuple(
        marker.position for marker in state.unresolved_markers.values()
    ) + tuple(
        german_unit.position
        for german_unit in state.german_units.values()
        if german_unit.status is GermanUnitStatus.ACTIVE
    )
    if not targets:
        return 0
    return min(_hex_distance(coord, target) for target in targets)


def _revealed_marker_count(destination: HexCoord, state: GameState) -> int:
    return sum(
        1
        for marker in state.unresolved_markers.values()
        if are_adjacent(destination, marker.position)
    )


def _is_adjacent_to_active_german(coord: HexCoord, state: GameState) -> bool:
    return any(
        german_unit.status is GermanUnitStatus.ACTIVE
        and are_adjacent(coord, german_unit.position)
        for german_unit in state.german_units.values()
    )


def _active_fire_zone_count(coord: HexCoord, state: GameState) -> int:
    return sum(
        1
        for german_unit in state.german_units.values()
        if german_unit.status is GermanUnitStatus.ACTIVE
        and coord in german_fire_zone_hexes(state.mission, german_unit)
    )


def _hypothetical_fire_zone_hexes(
    mission: Mission,
    marker_position: HexCoord,
    facing,
) -> tuple[HexCoord, ...]:
    hypothetical_unit = RevealedGermanUnitState(
        unit_id="hypothetical",
        unit_class="light_machine_gun",
        position=marker_position,
        facing=facing,
        status=GermanUnitStatus.ACTIVE,
    )
    return german_fire_zone_hexes(mission, hypothetical_unit)


def _terrain_bonus(coord: HexCoord, mission: Mission) -> int:
    map_hex = mission.map.hex_at(coord)
    if map_hex is None:
        return 0

    bonus = 0
    if map_hex.has_terrain(TerrainType.WOODS):
        bonus += 1
    if map_hex.has_terrain(TerrainType.HILL):
        bonus += 2
    if map_hex.has_terrain(TerrainType.BUILDING):
        bonus += 2
    return bonus


def _removed_german_count(state: GameState) -> int:
    return sum(
        1
        for german_unit in state.german_units.values()
        if german_unit.status is GermanUnitStatus.REMOVED
    )


def _two_d6_hit_probability(threshold: int) -> float:
    successes = 0
    for first_die in range(1, 7):
        for second_die in range(1, 7):
            if first_die + second_die >= threshold:
                successes += 1
    return successes / 36.0


def _hex_distance(first: HexCoord, second: HexCoord) -> int:
    delta_q = first.q - second.q
    delta_r = first.r - second.r
    delta_s = (first.q + first.r) - (second.q + second.r)
    return max(abs(delta_q), abs(delta_r), abs(delta_s))


def _tie_break_key(action: GameAction) -> tuple[str, str]:
    if isinstance(action, SelectBritishUnitAction):
        return (action.kind.value, action.unit_id)
    if isinstance(action, ResolveDoubleChoiceAction):
        return (action.kind.value, action.choice.value)
    if isinstance(action, SelectActivationDieAction):
        return (action.kind.value, str(action.die_value))
    if isinstance(action, DiscardActivationRollAction):
        return (action.kind.value, "")
    if isinstance(action, ChooseOrderExecutionAction):
        return (action.kind.value, action.choice.value)
    if isinstance(action, AdvanceAction):
        return (action.kind.value, f"{action.destination.q},{action.destination.r}")
    if isinstance(action, FireAction | GrenadeAttackAction):
        return (action.kind.value, action.target_unit_id)
    if isinstance(action, TakeCoverAction | RallyAction):
        return (action.kind.value, "")
    if isinstance(action, ScoutAction):
        facing = "" if action.facing is None else action.facing.value
        return (action.kind.value, f"{action.marker_id}:{facing}")
    if isinstance(action, SelectGermanUnitAction):
        return (action.kind.value, action.unit_id)
    raise AssertionError(f"Unsupported action type: {type(action)!r}")


__all__ = ["Mission3HeuristicAgent", "evaluate_mission3_state"]
