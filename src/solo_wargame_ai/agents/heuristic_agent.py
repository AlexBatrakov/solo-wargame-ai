"""Deterministic Mission 1 heuristic baseline for Phase 3 comparisons.

This agent is intentionally Mission-1-specific. It stays on the accepted Phase
3 contract by choosing from the provided legal action tuple, but it also uses
resolver-based lookahead plus a small amount of synthetic state fabrication to
score those legal actions. Treat it as an accepted baseline policy, not as a
general future-agent framework.
"""

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
from solo_wargame_ai.domain.hexgrid import HexCoord, are_adjacent
from solo_wargame_ai.domain.mission import Mission
from solo_wargame_ai.domain.resolver import apply_action, get_legal_actions
from solo_wargame_ai.domain.state import CurrentActivation, GameState
from solo_wargame_ai.domain.terrain import TerrainType
from solo_wargame_ai.domain.units import (
    BritishMorale,
    BritishUnitState,
    GermanUnitStatus,
    RevealedGermanUnitState,
)


class HeuristicAgent:
    """Prefer local progress, immediate attacks, and safer reveals."""

    name = "heuristic"

    def select_action(
        self,
        state: GameState,
        legal_actions: tuple[GameAction, ...],
    ) -> GameAction:
        if not legal_actions:
            raise ValueError("HeuristicAgent requires at least one legal action")

        return min(
            legal_actions,
            key=lambda action: (
                -self._score_action(state, action, depth=2),
                self._tie_break_key(action),
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
            SelectActivationDieAction | ChooseOrderExecutionAction | DiscardActivationRollAction,
        ):
            bonus = 8.0 if self._is_both_orders_choice(action) else 0.0
            if isinstance(action, DiscardActivationRollAction):
                bonus -= 12.0
            return score + bonus + self._lookahead_score(state, action, depth=depth)

        return score

    def _shallow_action_score(self, state: GameState, action: GameAction) -> float:
        if isinstance(action, SelectBritishUnitAction):
            return self._unit_priority_score(state, action.unit_id)
        if isinstance(action, ResolveDoubleChoiceAction):
            return 0.0
        if isinstance(action, SelectActivationDieAction):
            return 0.0
        if isinstance(action, DiscardActivationRollAction):
            return -12.0
        return self._base_action_score(state, action)

    def _lookahead_score(
        self,
        state: GameState,
        action: GameAction,
        *,
        depth: int,
    ) -> float:
        next_state = apply_action(state, action)
        next_legal_actions = get_legal_actions(next_state)
        if not next_legal_actions:
            return 0.0
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
            return 0.0
        if isinstance(action, ChooseOrderExecutionAction):
            return {
                OrderExecutionChoice.NO_ACTION: -25.0,
                OrderExecutionChoice.FIRST_ORDER_ONLY: 0.0,
                OrderExecutionChoice.SECOND_ORDER_ONLY: -2.0,
                OrderExecutionChoice.BOTH_ORDERS: 0.0,
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
            return -self._german_unit_threat(state, action.unit_id)
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
                self._score_action(synthetic_state, action, depth=1)
                for action in legal_actions
            )
        return total / 6.0

    def _unit_priority_score(self, state: GameState, unit_id: str) -> float:
        unit = state.british_units[unit_id]
        score = 24.0 - (4.0 * self._distance_to_objective(unit.position, state))
        if unit.morale is BritishMorale.LOW:
            score += 18.0
        if self._is_adjacent_to_active_german(unit.position, state):
            score += 16.0
        return score

    def _synthetic_order_execution_state(
        self,
        state: GameState,
        *,
        unit_id: str,
        die_value: int,
    ) -> GameState:
        # Phase 3 note: this fabricates a Mission 1 order-choice state outside
        # the normal transition path to estimate activation value. Revisit this
        # helper if later phases widen activation-state semantics.
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

        score = 55.0
        score += 12.0 * (
            self._distance_to_objective(current_position, state)
            - self._distance_to_objective(destination, state)
        )
        if self._reveals_hidden_marker(destination, state):
            score += 45.0
        if self._is_adjacent_to_active_german(destination, state):
            score += 28.0
        if self._terrain_at(destination, state.mission) is TerrainType.WOODS:
            score += 6.0
        score -= 8.0 * self._active_fire_zone_count(destination, state)
        if active_unit.morale is BritishMorale.LOW:
            score -= 10.0
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
        return 110.0 + (100.0 * self._two_d6_hit_probability(threshold))

    def _take_cover_score(self, state: GameState) -> float:
        active_unit = self._active_unit(state)
        threat_count = self._active_fire_zone_count(active_unit.position, state)
        threat_score = 18.0 * threat_count
        return 28.0 + threat_score - (4.0 * active_unit.cover)

    def _rally_score(self, state: GameState) -> float:
        active_unit = self._active_unit(state)
        if active_unit.morale is BritishMorale.LOW:
            return 95.0
        return -10.0

    def _scout_score(self, state: GameState, action: ScoutAction) -> float:
        marker = state.unresolved_markers[action.marker_id]
        exposed_british_units = sum(
            1
            for unit in state.british_units.values()
            if unit.morale is not BritishMorale.REMOVED
            and action.facing is not None
            and unit.position
            in self._hypothetical_fire_zone_hexes(
                state.mission,
                marker.position,
                action.facing,
            )
        )
        return 70.0 - (12.0 * exposed_british_units)

    def _german_unit_threat(self, state: GameState, unit_id: str) -> float:
        german_unit = state.german_units[unit_id]
        if german_unit.status is not GermanUnitStatus.ACTIVE:
            return -1.0
        fire_zone = frozenset(german_fire_zone_hexes(state.mission, german_unit))
        return sum(
            1.0
            for british_unit in state.british_units.values()
            if british_unit.morale is not BritishMorale.REMOVED
            and british_unit.position in fire_zone
            and are_adjacent(german_unit.position, british_unit.position)
        )

    def _active_unit(self, state: GameState) -> BritishUnitState:
        if state.current_activation is None:
            raise AssertionError("current activation is required to score this action")
        return state.british_units[state.current_activation.active_unit_id]

    def _distance_to_objective(self, coord: HexCoord, state: GameState) -> int:
        targets = tuple(
            marker.position for marker in state.unresolved_markers.values()
        ) + tuple(
            german_unit.position
            for german_unit in state.german_units.values()
            if german_unit.status is GermanUnitStatus.ACTIVE
        )
        if not targets:
            return 0
        return min(self._hex_distance(coord, target) for target in targets)

    def _reveals_hidden_marker(self, destination: HexCoord, state: GameState) -> bool:
        return any(
            are_adjacent(destination, marker.position)
            for marker in state.unresolved_markers.values()
        )

    def _is_adjacent_to_active_german(self, coord: HexCoord, state: GameState) -> bool:
        return any(
            german_unit.status is GermanUnitStatus.ACTIVE
            and are_adjacent(coord, german_unit.position)
            for german_unit in state.german_units.values()
        )

    def _active_fire_zone_count(self, coord: HexCoord, state: GameState) -> int:
        return sum(
            1
            for german_unit in state.german_units.values()
            if german_unit.status is GermanUnitStatus.ACTIVE
            and coord in german_fire_zone_hexes(state.mission, german_unit)
        )

    def _hypothetical_fire_zone_hexes(
        self,
        mission: Mission,
        marker_position: HexCoord,
        facing,
    ) -> tuple[HexCoord, ...]:
        # Reuse the accepted fire-zone helper instead of duplicating directional logic.
        hypothetical_unit = RevealedGermanUnitState(
            unit_id="hypothetical",
            unit_class="light_machine_gun",
            position=marker_position,
            facing=facing,
            status=GermanUnitStatus.ACTIVE,
        )
        return german_fire_zone_hexes(mission, hypothetical_unit)

    def _terrain_at(self, coord, mission: Mission) -> TerrainType | None:
        map_hex = mission.map.hex_at(coord)
        if map_hex is None:
            return None
        return map_hex.terrain

    def _two_d6_hit_probability(self, threshold: int) -> float:
        successes = 0
        for first_die in range(1, 7):
            for second_die in range(1, 7):
                if first_die + second_die >= threshold:
                    successes += 1
        return successes / 36.0

    def _hex_distance(self, first: HexCoord, second: HexCoord) -> int:
        delta_q = first.q - second.q
        delta_r = first.r - second.r
        delta_s = (first.q + first.r) - (second.q + second.r)
        return max(abs(delta_q), abs(delta_r), abs(delta_s))

    def _is_both_orders_choice(self, action: GameAction) -> bool:
        return isinstance(action, ChooseOrderExecutionAction) and (
            action.choice is OrderExecutionChoice.BOTH_ORDERS
        )

    def _tie_break_key(self, action: GameAction) -> tuple[str, str]:
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


__all__ = ["HeuristicAgent"]
