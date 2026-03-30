"""Promoted Mission 1/2 exact-guided heuristic successor.

This agent preserves the shipped :class:`HeuristicAgent` as the historical
Mission 1 baseline. The tracked successor productizes the strongest stable
Mission-1-led exact-guided line that survived local reruns:

- Mission 1 keeps the stable endgame, opening, and compact-table refinements.
- Mission 2 keeps only the later narrow transfer rules that survived into the
  shared promoted candidate.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import replace
from itertools import product

from solo_wargame_ai.domain.actions import (
    AdvanceAction,
    ChooseOrderExecutionAction,
    DiscardActivationRollAction,
    DoubleChoiceOption,
    FireAction,
    GameAction,
    GrenadeAttackAction,
    OrderExecutionChoice,
    ResolveDoubleChoiceAction,
    ScoutAction,
    SelectActivationDieAction,
)
from solo_wargame_ai.domain.combat import (
    calculate_fire_threshold,
    calculate_grenade_attack_threshold,
    german_fire_zone_hexes,
)
from solo_wargame_ai.domain.decision_context import (
    ChooseBritishUnitContext,
    ChooseGermanUnitContext,
    ChooseOrderParameterContext,
    DecisionContextKind,
)
from solo_wargame_ai.domain.enums import HexDirection
from solo_wargame_ai.domain.hexgrid import (
    HexCoord,
    are_adjacent,
    british_forward_neighbors,
)
from solo_wargame_ai.domain.legal_actions import lookup_orders_chart_row
from solo_wargame_ai.domain.mission import Mission, OrderName, OrdersChartRow
from solo_wargame_ai.domain.resolver import (
    get_legal_actions,
    resolve_automatic_progression,
)
from solo_wargame_ai.domain.reveal import (
    facing_toward_adjacent_hex,
    movement_reveal_marker_ids,
)
from solo_wargame_ai.domain.state import (
    GamePhase,
    GameState,
    TerminalOutcome,
    validate_game_state,
)
from solo_wargame_ai.domain.terrain import TerrainType
from solo_wargame_ai.domain.units import (
    BritishMorale,
    GermanUnitStatus,
    RevealedGermanUnitState,
)

from .heuristic_agent import HeuristicAgent

AGENDA_REVEAL_BLOCK_PENALTY = 140.0
AGENDA_SECOND_REVEAL_PENALTY = 80.0
AGENDA_ACTIVE_SCOUT_PENALTY = 120.0
AGENDA_STAGE_REWARD = 12.0
AGENDA_SUPPORT_BONUS = 12.0
AGENDA_ATTACK_THREAT_BONUS = 18.0
AGENDA_ENDGAME_RELIEF = 0.70

ENDGAME_EXPECTED_PLAN_WEIGHT = 0.28
ENDGAME_DIE_CHOICE_WEIGHT = 0.85
ENDGAME_ORDER_CHOICE_WEIGHT = 1.00
ENDGAME_KEEP_CHOICE_WEIGHT = 0.55
ENDGAME_REROLL_CHOICE_WEIGHT = 0.35
ENDGAME_DISCARD_PENALTY = 42.0
ENDGAME_NO_ACTION_PENALTY = 60.0
ENDGAME_URGENCY_FLOOR = 0.60

FLANK_BONUS = 18.0
FLANK_IN_ZONE_ADJACENT_PENALTY = 12.0
FLANK_FIRE_ZONE_ESCAPE_BONUS = 10.0
FLANK_FUTURE_ATTACK_BONUS = 18.0
FLANK_LOW_MORALE_EXTRA_PENALTY = 8.0
FLANK_NO_FOLLOWUP_IN_ZONE_PENALTY = 8.0

MISSION1_LEFT_LANE_BONUS = 26.0
MISSION1_CENTER_PENALTY = 24.0
MISSION1_STACK_RIGHT_PENALTY = 24.0
MISSION1_RIGHT_LANE_DOWN_LEFT_SCOUT_BONUS = 24.0
MISSION1_RIGHT_LANE_DOWN_SCOUT_PENALTY = 12.0

MISSION1_LEFT_SCOUT_DOWN_RIGHT_BONUS = 16.0
MISSION1_LEFT_SCOUT_DOWN_PENALTY = 12.0
MISSION1_SPLIT_RIGHT_BONUS = 16.0
MISSION1_STACK_LEFT_PENALTY = 12.0
MISSION1_SCOUT_ONLY_BONUS = 18.0
MISSION1_BOTH_ORDERS_PENALTY = 14.0
MISSION1_FIRST_ONLY_PENALTY = 8.0

MISSION1_HIDDEN_REROLL_BONUS = 16.0
MISSION1_HIDDEN_KEEP_PENALTY = 12.0
MISSION1_LOW_FORWARD_UNIT_PENALTY = 16.0
MISSION1_HEALTHY_RELAY_BONUS = 12.0
MISSION1_OPENING_TABLE_SCALE = 100.0
MISSION1_HIDDEN_DOUBLE_TABLE_SCALE = 600.0

MISSION2_LMG_DIE63_BONUS = 110.0
MISSION2_ROLL22_ONE_TWO_BONUS = 80.0
MISSION2_ROLL22_MINUS_ONE_THREE_PENALTY = 60.0
MISSION2_ROLL25_ZERO_TWO_BONUS = 65.0
MISSION2_ROLL25_MINUS_ONE_THREE_PENALTY = 45.0

MISSION2_TURN2_ADVANCE_BONUS = 100.0
MISSION2_TURN2_ADVANCE_PENALTY = 70.0
MISSION2_TURN2_SCOUT_BONUS = 110.0
MISSION2_TURN2_SCOUT_PENALTY = 80.0

MISSION2_TURN2_LEFT_DOWN_RIGHT_BONUS = 105.0
MISSION2_TURN2_LEFT_DOWN_PENALTY = 85.0
MISSION2_TURN2_LEFT_DOWN_LEFT_PENALTY = 70.0

MISSION2_LATE_LEFT_DOWN_RIGHT_BONUS = 85.0
MISSION2_LATE_LEFT_DOWN_PENALTY = 70.0
MISSION2_LATE_LEFT_DOWN_LEFT_PENALTY = 60.0

MISSION2_ACTIVATION_DIE_TABLE_BONUS = 120.0

MISSION1_OPENING_TABLE = {
    2: {
        "-1,3": 0.08095107720425698,
        "0,2": -0.1169283383799683,
        "1,2": 0.035977261175711206,
    },
    3: {
        "-1,3": -0.005318929185485377,
        "0,2": -0.0530418997674742,
        "1,2": 0.058360828952959465,
    },
    5: {
        "-1,3": 0.005801707567891223,
        "0,2": -0.0752831732742274,
        "1,2": 0.06948146570633607,
    },
    6: {
        "-1,3": -0.014555489184852832,
        "0,2": -0.034568779768739066,
        "1,2": 0.04912426895359201,
    },
}

MISSION1_HIDDEN_DOUBLE_TABLE = {
    (
        "rifle_squad_a",
        (-1, 3),
        "rifle_squad_b",
        (-1, 3),
        1,
        2,
        "advance+scout",
    ): {
        "keep": 0.041950102436254855,
        "reroll": -0.041950102436254966,
    },
    (
        "rifle_squad_b",
        (0, 3),
        "rifle_squad_a",
        (-1, 3),
        None,
        3,
        "advance+take_cover",
    ): {
        "keep": -0.007618072735359083,
        "reroll": 0.007618072735358972,
    },
    (
        "rifle_squad_b",
        (0, 3),
        "rifle_squad_a",
        (-1, 3),
        None,
        6,
        "advance+fire",
    ): {
        "keep": -0.007618072735359083,
        "reroll": 0.007618072735358972,
    },
    (
        "rifle_squad_a",
        (0, 3),
        "rifle_squad_b",
        (0, 3),
        0,
        3,
        "advance+take_cover",
    ): {
        "keep": -0.0048527941226558235,
        "reroll": 0.0048527941226558235,
    },
}

MISSION2_ACTIVATION_DIE_TABLE = {
    (
        "turn=1|active=rifle_squad_b|roll=(2, 6)|british=rifle_squad_a@(0,2)/normal/c0 ; "
        "rifle_squad_b@(0,3)/normal/c0|active_german=light_machine_gun@(-1,2)/down_right|"
        "removed=-|markers=qm_1@(0,0)"
    ): (6,),
    (
        "turn=1|active=rifle_squad_b|roll=(2, 6)|british=rifle_squad_a@(0,2)/normal/c1 ; "
        "rifle_squad_b@(0,3)/normal/c0|active_german=light_machine_gun@(-1,2)/down_right|"
        "removed=-|markers=qm_1@(0,0)"
    ): (6,),
    (
        "turn=1|active=rifle_squad_b|roll=(3, 6)|british=rifle_squad_a@(0,2)/normal/c1 ; "
        "rifle_squad_b@(0,3)/normal/c0|active_german=heavy_machine_gun@(-1,2)/down_right|"
        "removed=-|markers=qm_1@(0,0)"
    ): (6,),
    (
        "turn=1|active=rifle_squad_b|roll=(3, 6)|british=rifle_squad_a@(0,2)/normal/c1 ; "
        "rifle_squad_b@(0,3)/normal/c0|active_german=light_machine_gun@(-1,2)/down_right|"
        "removed=-|markers=qm_1@(0,0)"
    ): (6,),
    (
        "turn=1|active=rifle_squad_b|roll=(3, 6)|british=rifle_squad_a@(0,2)/normal/c0 ; "
        "rifle_squad_b@(0,3)/normal/c0|active_german=heavy_machine_gun@(-1,2)/down_right|"
        "removed=-|markers=qm_1@(0,0)"
    ): (6,),
    (
        "turn=2|active=rifle_squad_b|roll=(2, 3)|british=rifle_squad_a@(0,2)/low/c0 ; "
        "rifle_squad_b@(-1,3)/normal/c0|active_german=heavy_machine_gun@(-1,2)/down_right|"
        "removed=-|markers=qm_1@(0,0)"
    ): (2,),
}


class _AgendaHeuristicBase(HeuristicAgent):
    """Mission-family agenda layer used as the promoted agent base and leaf scorer."""

    def __init__(self, *, name: str) -> None:
        self.name = name
        self._mission_cache: dict[str, tuple[dict[str, float], dict[str, float]]] = {}

    def _mission_tables(self, mission: Mission) -> tuple[dict[str, float], dict[str, float]]:
        cached = self._mission_cache.get(mission.mission_id)
        if cached is not None:
            return cached

        reveal_probs = Counter()
        for row in mission.german.reveal_table:
            reveal_probs[row.result_unit_class] += (row.roll_max - row.roll_min + 1) / 6.0

        class_threat: dict[str, float] = {}
        for unit_class, probability in reveal_probs.items():
            german_class = mission.german.unit_classes_by_name[unit_class]
            class_threat[unit_class] = self._two_d6_hit_probability(german_class.attack_to_hit)
            if german_class.uses_fire_zone:
                class_threat[unit_class] += 0.20
            if probability <= 0.0:
                class_threat[unit_class] = 0.0

        result = (dict(reveal_probs), class_threat)
        self._mission_cache[mission.mission_id] = result
        return result

    def _turn_pressure(self, state: GameState) -> float:
        max_extra_turns = max(1, state.mission.turns.turn_limit - 1)
        progress = max(0, state.turn - 1) / max_extra_turns
        return min(1.0, progress)

    def _active_german_units(self, state: GameState) -> tuple[RevealedGermanUnitState, ...]:
        return tuple(
            german_unit
            for german_unit in state.german_units.values()
            if german_unit.status is GermanUnitStatus.ACTIVE
        )

    def _support_bonus(self, coord: HexCoord, state: GameState, *, active_unit_id: str) -> float:
        best = 0.0
        for unit_id, british_unit in state.british_units.items():
            if unit_id == active_unit_id or british_unit.morale is BritishMorale.REMOVED:
                continue
            distance = self._hex_distance(coord, british_unit.position)
            if distance <= 1:
                best = max(best, AGENDA_SUPPORT_BONUS)
            elif distance == 2:
                best = max(best, AGENDA_SUPPORT_BONUS / 2.0)
        return best

    def _support_ready_for_marker(self, marker_position: HexCoord, state: GameState) -> float:
        return sum(
            1.0
            for british_unit in state.british_units.values()
            if british_unit.morale is not BritishMorale.REMOVED
            and self._hex_distance(british_unit.position, marker_position) <= 1
        )

    def _has_followup_attack(self, state: GameState) -> bool:
        activation = state.current_activation
        if activation is None:
            return False
        if activation.next_order_index + 1 >= len(activation.planned_orders):
            return False
        next_order = activation.planned_orders[activation.next_order_index + 1]
        return next_order in (OrderName.FIRE, OrderName.GRENADE_ATTACK)

    def _expected_hidden_exposure_after_advance(
        self,
        state: GameState,
        destination: HexCoord,
    ) -> float:
        reveal_ids = movement_reveal_marker_ids(state, destination)
        if not reveal_ids:
            return 0.0

        reveal_probs, class_threat = self._mission_tables(state.mission)
        active_unit = self._active_unit(state)
        total = 0.0

        for marker_id in reveal_ids:
            marker = state.unresolved_markers[marker_id]
            facing = facing_toward_adjacent_hex(marker.position, destination)
            for unit_class, probability in reveal_probs.items():
                hypothetical = RevealedGermanUnitState(
                    unit_id="hypothetical",
                    unit_class=unit_class,
                    position=marker.position,
                    facing=facing,
                    status=GermanUnitStatus.ACTIVE,
                )
                fire_zone = frozenset(german_fire_zone_hexes(state.mission, hypothetical))
                exposed = 0.0
                for british_unit in state.british_units.values():
                    if british_unit.morale is BritishMorale.REMOVED:
                        continue
                    projected_position = (
                        destination
                        if british_unit.unit_id == active_unit.unit_id
                        else british_unit.position
                    )
                    if projected_position in fire_zone:
                        exposed += 1.0
                total += probability * class_threat[unit_class] * exposed
        return total

    def _stage_value(self, coord: HexCoord, state: GameState) -> float:
        if not state.unresolved_markers:
            return 0.0
        total = 0.0
        for marker in state.unresolved_markers.values():
            distance = self._hex_distance(coord, marker.position)
            if distance == 2:
                total += 1.0
            elif distance == 1:
                total += 0.5
        return total

    def _active_threat_distance(self, coord: HexCoord, state: GameState) -> int:
        active_units = self._active_german_units(state)
        if not active_units:
            return 0
        return min(self._hex_distance(coord, german_unit.position) for german_unit in active_units)

    def _objective_pressure(self, coord: HexCoord, state: GameState) -> float:
        active_units = self._active_german_units(state)
        if active_units:
            return sum(
                max(0, 4 - self._hex_distance(coord, german_unit.position))
                for german_unit in active_units
            )
        return sum(
            max(0, 4 - self._hex_distance(coord, marker.position))
            for marker in state.unresolved_markers.values()
        )

    def _unit_priority_score(self, state: GameState, unit_id: str) -> float:
        unit = state.british_units[unit_id]
        active_units = self._active_german_units(state)
        if active_units:
            score = 26.0 + (7.0 * self._objective_pressure(unit.position, state))
            score += self._support_bonus(unit.position, state, active_unit_id=unit_id)
            if unit.morale is BritishMorale.LOW:
                score += 18.0
            if self._is_adjacent_to_active_german(unit.position, state):
                score += 18.0
            return score

        score = 20.0 + (5.0 * self._stage_value(unit.position, state))
        score += self._support_bonus(unit.position, state, active_unit_id=unit_id)
        if unit.morale is BritishMorale.LOW:
            score += 8.0
        return score

    def _advance_score(self, state: GameState, action: AdvanceAction) -> float:
        active_unit = self._active_unit(state)
        current_position = active_unit.position
        destination = action.destination
        reveal_count = len(movement_reveal_marker_ids(state, destination))
        support_bonus = self._support_bonus(destination, state, active_unit_id=active_unit.unit_id)
        active_fire_penalty = 8.0 * self._active_fire_zone_count(destination, state)
        hidden_exposure = self._expected_hidden_exposure_after_advance(state, destination)
        turn_pressure = self._turn_pressure(state)
        has_followup_attack = self._has_followup_attack(state)
        active_units = self._active_german_units(state)

        if active_units:
            score = 36.0
            score += 12.0 * (
                self._active_threat_distance(current_position, state)
                - self._active_threat_distance(destination, state)
            )
            score += support_bonus
            score -= active_fire_penalty
            if self._terrain_at(destination, state.mission) is TerrainType.WOODS:
                score += 5.0
            if self._is_adjacent_to_active_german(destination, state):
                score += 18.0
            if reveal_count:
                score -= (
                    AGENDA_REVEAL_BLOCK_PENALTY
                    * reveal_count
                    * (1.0 - AGENDA_ENDGAME_RELIEF * turn_pressure)
                )
                if not has_followup_attack:
                    score -= 0.5 * AGENDA_REVEAL_BLOCK_PENALTY * reveal_count
                score -= 14.0 * hidden_exposure
                if reveal_count > 1:
                    score -= AGENDA_SECOND_REVEAL_PENALTY * (reveal_count - 1)
            if active_unit.morale is BritishMorale.LOW:
                score -= 8.0
            return score

        score = 42.0
        score += 8.0 * self._stage_value(destination, state)
        score += 6.0 * (
            self._objective_pressure(destination, state)
            - self._objective_pressure(current_position, state)
        )
        score += support_bonus
        score -= active_fire_penalty
        if self._terrain_at(destination, state.mission) is TerrainType.WOODS:
            score += 4.0
        if reveal_count == 0:
            score += AGENDA_STAGE_REWARD
        else:
            score += 24.0 * min(1, reveal_count)
            score -= 10.0 * hidden_exposure
            if reveal_count > 1 and turn_pressure < 0.95:
                score -= AGENDA_SECOND_REVEAL_PENALTY * (reveal_count - 1)
            if support_bonus <= 0.0 and turn_pressure < 0.85:
                score -= 24.0 * reveal_count
            if has_followup_attack:
                score += 12.0 * reveal_count
        if active_unit.morale is BritishMorale.LOW:
            score -= 8.0
        return score

    def _scout_score(self, state: GameState, action: ScoutAction) -> float:
        marker = state.unresolved_markers[action.marker_id]
        support_ready = self._support_ready_for_marker(marker.position, state)
        turn_pressure = self._turn_pressure(state)
        if self._active_german_units(state):
            return -AGENDA_ACTIVE_SCOUT_PENALTY * (1.0 - AGENDA_ENDGAME_RELIEF * turn_pressure)
        score = 58.0 + (8.0 * support_ready)
        if support_ready < 1.5 and turn_pressure < 0.85:
            score -= 18.0
        return score

    def _attack_score(
        self,
        state: GameState,
        action: FireAction | GrenadeAttackAction,
    ) -> float:
        base_score = super()._attack_score(state, action)
        _reveal_probs, class_threat = self._mission_tables(state.mission)
        target = state.german_units[action.target_unit_id]
        return base_score + (AGENDA_ATTACK_THREAT_BONUS * class_threat[target.unit_class])

    def _take_cover_score(self, state: GameState) -> float:
        active_unit = self._active_unit(state)
        base_score = super()._take_cover_score(state)
        if self._active_german_units(state) and active_unit.morale is BritishMorale.LOW:
            return base_score + 18.0
        return base_score

    def _german_unit_threat(self, state: GameState, unit_id: str) -> float:
        base_score = super()._german_unit_threat(state, unit_id)
        german_unit = state.german_units[unit_id]
        if german_unit.status is not GermanUnitStatus.ACTIVE:
            return base_score
        _reveal_probs, class_threat = self._mission_tables(state.mission)
        return base_score + (10.0 * class_threat[german_unit.unit_class])


class ExactGuidedHeuristicAgent(_AgendaHeuristicBase):
    """Mission 1/2 promoted successor to the historical HeuristicAgent."""

    name = "exact-guided-heuristic"

    def __init__(self) -> None:
        super().__init__(name=self.name)
        self._leaf_agent = _AgendaHeuristicBase(name="agenda-leaf")

    def _progress_to_decision(self, state: GameState) -> GameState:
        progressed = state
        while progressed.terminal_outcome is None:
            legal_actions = get_legal_actions(progressed)
            if legal_actions:
                return progressed
            progressed = resolve_automatic_progression(progressed)
        return progressed

    def _continuation_leaf_value(self, state: GameState) -> float:
        progressed = self._progress_to_decision(state)
        if progressed.terminal_outcome is TerminalOutcome.VICTORY:
            return 180.0
        if progressed.terminal_outcome is TerminalOutcome.DEFEAT:
            return -180.0
        legal_actions = get_legal_actions(progressed)
        if not legal_actions:
            return 0.0
        return max(
            self._leaf_agent._score_action(progressed, action, depth=2)
            for action in legal_actions
        )

    def _continue_after_resolved_order_preview(
        self,
        state: GameState,
        *,
        british_units,
        german_units,
        unresolved_markers,
        rng_state,
    ) -> GameState:
        activation = state.current_activation
        if activation is None:
            raise AssertionError("current activation is required to preview order continuation")

        next_order_index = activation.next_order_index + 1
        updated_state = replace(
            state,
            british_units=british_units,
            german_units=german_units,
            unresolved_markers=unresolved_markers,
            rng_state=rng_state,
        )

        while next_order_index < len(activation.planned_orders):
            next_order = activation.planned_orders[next_order_index]
            next_state = replace(
                updated_state,
                pending_decision=ChooseOrderParameterContext(
                    order=next_order,
                    order_index=next_order_index,
                ),
                current_activation=replace(
                    activation,
                    next_order_index=next_order_index,
                ),
            )
            if get_legal_actions(next_state):
                validate_game_state(next_state)
                return next_state
            next_order_index += 1

        activated_unit_ids = frozenset(
            (*updated_state.activated_british_unit_ids, activation.active_unit_id),
        )
        choose_british_state = replace(
            updated_state,
            activated_british_unit_ids=activated_unit_ids,
            pending_decision=ChooseBritishUnitContext(),
            current_activation=None,
        )
        if get_legal_actions(choose_british_state):
            validate_game_state(choose_british_state)
            return choose_british_state

        choose_german_state = replace(
            updated_state,
            phase=GamePhase.GERMAN,
            activated_british_unit_ids=activated_unit_ids,
            activated_german_unit_ids=frozenset(),
            pending_decision=ChooseGermanUnitContext(),
            current_activation=None,
        )
        validate_game_state(choose_german_state)
        return choose_german_state

    def _expected_reveal_continuation_after_advance(
        self,
        state: GameState,
        action: AdvanceAction,
    ) -> float:
        activation = state.current_activation
        if activation is None:
            return 0.0

        active_unit = state.british_units[activation.active_unit_id]
        british_units = dict(state.british_units)
        british_units[active_unit.unit_id] = replace(
            active_unit,
            position=action.destination,
            cover=0,
        )

        marker_ids = movement_reveal_marker_ids(state, action.destination)
        if not marker_ids:
            next_state = self._continue_after_resolved_order_preview(
                state,
                british_units=british_units,
                german_units=state.german_units,
                unresolved_markers=state.unresolved_markers,
                rng_state=state.rng_state,
            )
            return self._continuation_leaf_value(next_state)

        reveal_probs, _class_threat = self._mission_tables(state.mission)
        unresolved_markers = dict(state.unresolved_markers)
        total = 0.0
        marker_states = tuple(state.unresolved_markers[marker_id] for marker_id in marker_ids)
        marker_probs = tuple(reveal_probs.items())
        for marker_assignment in product(marker_probs, repeat=len(marker_ids)):
            probability = 1.0
            german_units = dict(state.german_units)
            unresolved_after_reveal = dict(unresolved_markers)
            for marker_id, marker_state, (unit_class, unit_probability) in zip(
                marker_ids,
                marker_states,
                marker_assignment,
                strict=True,
            ):
                probability *= unit_probability
                unresolved_after_reveal.pop(marker_id)
                german_units[marker_id] = RevealedGermanUnitState(
                    unit_id=marker_id,
                    unit_class=unit_class,
                    position=marker_state.position,
                    facing=facing_toward_adjacent_hex(marker_state.position, action.destination),
                    status=GermanUnitStatus.ACTIVE,
                )
            next_state = self._continue_after_resolved_order_preview(
                state,
                british_units=british_units,
                german_units=german_units,
                unresolved_markers=unresolved_after_reveal,
                rng_state=state.rng_state,
            )
            total += probability * self._continuation_leaf_value(next_state)
        return total

    def _expected_reveal_continuation_after_scout(
        self,
        state: GameState,
        action: ScoutAction,
    ) -> float:
        marker_state = state.unresolved_markers[action.marker_id]
        reveal_probs, _class_threat = self._mission_tables(state.mission)
        unresolved_markers = dict(state.unresolved_markers)
        unresolved_markers.pop(action.marker_id)

        total = 0.0
        for unit_class, probability in reveal_probs.items():
            german_units = dict(state.german_units)
            german_units[action.marker_id] = RevealedGermanUnitState(
                unit_id=action.marker_id,
                unit_class=unit_class,
                position=marker_state.position,
                facing=action.facing,
                status=GermanUnitStatus.ACTIVE,
            )
            next_state = self._continue_after_resolved_order_preview(
                state,
                british_units=state.british_units,
                german_units=german_units,
                unresolved_markers=unresolved_markers,
                rng_state=state.rng_state,
            )
            total += probability * self._continuation_leaf_value(next_state)
        return total

    def _staging_setup_bonus(
        self,
        destination: HexCoord,
        state: GameState,
        *,
        active_unit_id: str,
    ) -> float:
        if self._active_german_units(state):
            return 0.0
        if not state.unresolved_markers:
            return 0.0

        bonus = 0.0
        other_units = [
            unit
            for unit_id, unit in state.british_units.items()
            if unit_id != active_unit_id and unit.morale is not BritishMorale.REMOVED
        ]
        for marker in state.unresolved_markers.values():
            distance = self._hex_distance(destination, marker.position)
            if distance == 2:
                bonus += 10.0
                if any(
                    self._hex_distance(unit.position, marker.position) <= 2
                    for unit in other_units
                ):
                    bonus += 6.0
            elif distance == 3:
                bonus += 2.0
        return bonus

    def _endgame_urgency(self, state: GameState) -> float:
        return max(ENDGAME_URGENCY_FLOOR, self._turn_pressure(state))

    def _critical_single_active_target(self, state: GameState):
        active_units = self._active_german_units(state)
        if len(active_units) != 1:
            return None
        if state.unresolved_markers:
            return None
        return active_units[0]

    def _legal_forward_destinations(
        self,
        position: HexCoord,
        state: GameState,
    ) -> tuple[HexCoord, ...]:
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
            if state.mission.map.is_playable_hex(destination)
            and destination not in occupied_by_german
        )

    def _attack_probability(
        self,
        state: GameState,
        *,
        attacker_position: HexCoord,
        attacker_cover: int,
        attack_order: OrderName,
        target_unit_id: str,
    ) -> float:
        target = state.german_units[target_unit_id]
        if target.status is not GermanUnitStatus.ACTIVE:
            return 0.0
        if not are_adjacent(attacker_position, target.position):
            return 0.0

        active_unit = self._active_unit(state)
        attacker = replace(active_unit, position=attacker_position, cover=attacker_cover)
        british_units = dict(state.british_units)
        british_units[attacker.unit_id] = attacker

        if attack_order is OrderName.FIRE:
            threshold = calculate_fire_threshold(
                state.mission,
                attacker=attacker,
                defender=target,
                british_units=british_units,
            )
        elif attack_order is OrderName.GRENADE_ATTACK:
            threshold = calculate_grenade_attack_threshold(
                state.mission,
                attacker=attacker,
            )
        else:
            return 0.0
        return self._two_d6_hit_probability(threshold)

    def _planned_orders_for_choice(
        self,
        row: OrdersChartRow,
        choice: OrderExecutionChoice,
    ) -> tuple[OrderName, ...]:
        if choice is OrderExecutionChoice.FIRST_ORDER_ONLY:
            return (row.first_order,)
        if choice is OrderExecutionChoice.SECOND_ORDER_ONLY:
            assert row.second_order is not None
            return (row.second_order,)
        if choice is OrderExecutionChoice.BOTH_ORDERS:
            assert row.second_order is not None
            return (row.first_order, row.second_order)
        if choice is OrderExecutionChoice.NO_ACTION:
            return ()
        raise AssertionError(f"Unsupported order execution choice: {choice!r}")

    def _best_advance_destination(
        self,
        state: GameState,
        *,
        position: HexCoord,
        target_position: HexCoord,
        future_attack_order: OrderName | None,
        attacker_cover: int,
        target_unit_id: str,
    ) -> tuple[HexCoord | None, float, int]:
        destinations = self._legal_forward_destinations(position, state)
        if not destinations:
            return None, 0.0, 0

        start_distance = self._hex_distance(position, target_position)
        best_tuple = None
        best_destination = None
        best_attack_probability = 0.0
        best_distance_gain = 0

        for destination in destinations:
            attack_probability = 0.0
            if future_attack_order is not None:
                attack_probability = self._attack_probability(
                    state,
                    attacker_position=destination,
                    attacker_cover=0,
                    attack_order=future_attack_order,
                    target_unit_id=target_unit_id,
                )
            distance_gain = max(
                0,
                start_distance - self._hex_distance(destination, target_position),
            )
            woods_bonus = (
                1
                if self._terrain_at(destination, state.mission) is TerrainType.WOODS
                else 0
            )
            fire_penalty = self._active_fire_zone_count(destination, state)
            candidate = (
                attack_probability,
                distance_gain,
                woods_bonus,
                -fire_penalty,
            )
            if best_tuple is None or candidate > best_tuple:
                best_tuple = candidate
                best_destination = destination
                best_attack_probability = attack_probability
                best_distance_gain = distance_gain

        return best_destination, best_attack_probability, best_distance_gain

    def _endgame_plan_score(
        self,
        state: GameState,
        *,
        planned_orders: tuple[OrderName, ...],
    ) -> float:
        activation = state.current_activation
        target = self._critical_single_active_target(state)
        if activation is None or target is None:
            return 0.0

        active_unit = self._active_unit(state)
        current_position = active_unit.position
        current_cover = active_unit.cover
        start_distance = self._hex_distance(current_position, target.position)
        best_kill_probability = 0.0
        total_distance_gain = 0
        took_cover = False
        rallied = False

        for index, order in enumerate(planned_orders):
            if order is OrderName.ADVANCE:
                future_attack_order = None
                for later_order in planned_orders[index + 1 :]:
                    if later_order in (OrderName.FIRE, OrderName.GRENADE_ATTACK):
                        future_attack_order = later_order
                        break
                (
                    destination,
                    future_attack_probability,
                    distance_gain,
                ) = self._best_advance_destination(
                    state,
                    position=current_position,
                    target_position=target.position,
                    future_attack_order=future_attack_order,
                    attacker_cover=current_cover,
                    target_unit_id=target.unit_id,
                )
                if destination is None:
                    continue
                current_position = destination
                current_cover = 0
                total_distance_gain += distance_gain
                best_kill_probability = max(best_kill_probability, future_attack_probability)
                continue

            if order in (OrderName.FIRE, OrderName.GRENADE_ATTACK):
                attack_probability = self._attack_probability(
                    state,
                    attacker_position=current_position,
                    attacker_cover=current_cover,
                    attack_order=order,
                    target_unit_id=target.unit_id,
                )
                best_kill_probability = max(best_kill_probability, attack_probability)
                continue

            if order is OrderName.TAKE_COVER:
                took_cover = True
                current_cover += 1
                continue

            if order is OrderName.RALLY:
                rallied = True

        final_distance = self._hex_distance(current_position, target.position)
        total_distance_gain = max(total_distance_gain, start_distance - final_distance)
        urgency = self._endgame_urgency(state)

        score = 240.0 * urgency * best_kill_probability
        score += 16.0 * urgency * total_distance_gain
        if took_cover and self._active_fire_zone_count(current_position, state) > 0:
            score += 10.0 * urgency
        if rallied and active_unit.morale is BritishMorale.LOW:
            score += 14.0 * urgency
        if not planned_orders:
            score -= ENDGAME_NO_ACTION_PENALTY * urgency
        return score

    def _best_endgame_choice_score(self, state: GameState) -> float:
        if self._critical_single_active_target(state) is None:
            return 0.0

        legal_actions = tuple(
            action
            for action in get_legal_actions(state)
            if isinstance(action, ChooseOrderExecutionAction)
        )
        if not legal_actions:
            return 0.0

        activation = state.current_activation
        if activation is None or activation.selected_die is None:
            return 0.0
        row = lookup_orders_chart_row(
            state.mission,
            unit_class=self._active_unit(state).unit_class,
            die_value=activation.selected_die,
        )
        return max(
            self._endgame_plan_score(
                state,
                planned_orders=self._planned_orders_for_choice(row, action.choice),
            )
            for action in legal_actions
        )

    def _synthetic_endgame_choice_score(
        self,
        state: GameState,
        *,
        unit_id: str,
        die_value: int,
    ) -> float:
        synthetic_state = self._synthetic_order_execution_state(
            state,
            unit_id=unit_id,
            die_value=die_value,
        )
        return self._best_endgame_choice_score(synthetic_state)

    def _expected_activation_value(self, state: GameState, unit_id: str) -> float:
        base_value = super()._expected_activation_value(state, unit_id)
        if self._critical_single_active_target(state) is None:
            return base_value
        total = 0.0
        for die_value in range(1, 7):
            total += self._synthetic_endgame_choice_score(
                state,
                unit_id=unit_id,
                die_value=die_value,
            )
        return base_value + (ENDGAME_EXPECTED_PLAN_WEIGHT * total / 6.0)

    def _opening_has_followup_scout(self, state: GameState) -> bool:
        activation = state.current_activation
        if activation is None:
            return False
        if activation.next_order_index + 1 >= len(activation.planned_orders):
            return False
        return activation.planned_orders[activation.next_order_index + 1] is OrderName.SCOUT

    def _is_mission1_opening_hidden_only(self, state: GameState) -> bool:
        return (
            state.mission.mission_id == "mission_01_secure_the_woods_1"
            and state.turn == 1
            and len(state.unresolved_markers) == 1
            and not self._active_german_units(state)
        )

    def _is_mission1_hidden_only(self, state: GameState) -> bool:
        return (
            state.mission.mission_id == "mission_01_secure_the_woods_1"
            and len(state.unresolved_markers) == 1
            and not self._active_german_units(state)
        )

    def _other_live_positions(
        self,
        state: GameState,
        *,
        active_unit_id: str,
    ) -> set[HexCoord]:
        return {
            unit.position
            for unit_id, unit in state.british_units.items()
            if unit_id != active_unit_id and unit.morale is not BritishMorale.REMOVED
        }

    def _mission1_hidden_double_window(self, state: GameState) -> bool:
        if state.mission.mission_id != "mission_01_secure_the_woods_1":
            return False
        if self._active_german_units(state):
            return False
        if len(state.unresolved_markers) != 1:
            return False
        if state.turn > 2:
            return False
        activation = state.current_activation
        if activation is None:
            return False
        return activation.roll[0] == activation.roll[1]

    def _mission1_single_active_unit_window(self, state: GameState) -> bool:
        if state.mission.mission_id != "mission_01_secure_the_woods_1":
            return False
        if state.turn > 2:
            return False
        target = self._critical_single_active_target(state)
        if target is None:
            return False
        live_units = [
            unit
            for unit in state.british_units.values()
            if unit.morale is not BritishMorale.REMOVED
        ]
        return len(live_units) == 2 and sum(
            unit.morale is BritishMorale.LOW for unit in live_units
        ) == 1

    def _mission1_opening_table_key(self, state: GameState) -> int | None:
        if state.mission.mission_id != "mission_01_secure_the_woods_1":
            return None
        if state.turn != 1:
            return None
        if len(state.unresolved_markers) != 1:
            return None
        if self._active_german_units(state):
            return None

        activation = state.current_activation
        if activation is None or activation.selected_die not in MISSION1_OPENING_TABLE:
            return None

        active_unit = self._active_unit(state)
        if active_unit.unit_id != "rifle_squad_b":
            return None
        if active_unit.position != HexCoord(0, 3):
            return None

        other_positions = {
            unit.position
            for unit_id, unit in state.british_units.items()
            if unit_id != active_unit.unit_id and unit.morale is not BritishMorale.REMOVED
        }
        if HexCoord(-1, 3) not in other_positions:
            return None
        return activation.selected_die

    def _current_row_signature(self, state: GameState) -> str | None:
        activation = state.current_activation
        if activation is None or activation.selected_die is None:
            return None
        active_unit = state.british_units[activation.active_unit_id]
        row = lookup_orders_chart_row(
            state.mission,
            unit_class=active_unit.unit_class,
            die_value=activation.selected_die,
        )
        second = "-" if row.second_order is None else row.second_order.value
        return f"{row.first_order.value}+{second}"

    def _mission1_hidden_double_table_scores(
        self,
        state: GameState,
    ) -> dict[str, float] | None:
        if state.mission.mission_id != "mission_01_secure_the_woods_1":
            return None
        if state.turn > 2:
            return None
        if len(state.unresolved_markers) != 1:
            return None
        if self._active_german_units(state):
            return None

        activation = state.current_activation
        if activation is None or activation.roll[0] != activation.roll[1]:
            return None

        active_unit = self._active_unit(state)
        live_others = [
            unit
            for unit_id, unit in state.british_units.items()
            if unit_id != active_unit.unit_id and unit.morale is not BritishMorale.REMOVED
        ]
        if len(live_others) != 1:
            return None
        other_unit = live_others[0]

        row = lookup_orders_chart_row(
            state.mission,
            unit_class=active_unit.unit_class,
            die_value=activation.roll[0],
        )
        row_signature = (
            f"{row.first_order.value}+"
            f"{row.second_order.value if row.second_order else '-'}"
        )
        key = (
            active_unit.unit_id,
            (active_unit.position.q, active_unit.position.r),
            other_unit.unit_id,
            (other_unit.position.q, other_unit.position.r),
            (
                other_unit.cover
                if active_unit.unit_id == "rifle_squad_a"
                and other_unit.position == HexCoord(-1, 3)
                else None
            ),
            activation.roll[0],
            row_signature,
        )
        return MISSION1_HIDDEN_DOUBLE_TABLE.get(key)

    def _mission2_active_german(self, state: GameState):
        active = [
            unit
            for unit in state.german_units.values()
            if unit.status is GermanUnitStatus.ACTIVE
        ]
        return active[0] if len(active) == 1 else None

    def _is_mission2_opening_mixed_b_anchor(self, state: GameState) -> bool:
        if state.mission.mission_id != "mission_02_secure_the_woods_2":
            return False
        if state.turn != 1:
            return False
        activation = state.current_activation
        if activation is None or activation.active_unit_id != "rifle_squad_b":
            return False
        if len(state.unresolved_markers) != 1 or "qm_1" not in state.unresolved_markers:
            return False
        marker = state.unresolved_markers["qm_1"]
        if marker.position != HexCoord(0, 0):
            return False
        active_german = self._mission2_active_german(state)
        if active_german is None:
            return False
        if active_german.position != HexCoord(-1, 2):
            return False
        if active_german.facing is not HexDirection.DOWN_RIGHT:
            return False
        positions = {
            unit_id: (unit.position, unit.morale, unit.cover)
            for unit_id, unit in state.british_units.items()
            if unit.morale is not BritishMorale.REMOVED
        }
        return positions == {
            "rifle_squad_a": (HexCoord(0, 2), BritishMorale.NORMAL, 0),
            "rifle_squad_b": (HexCoord(0, 3), BritishMorale.NORMAL, 0),
        }

    def _is_mission2_turn2_advance_scout_family(self, state: GameState) -> bool:
        if state.mission.mission_id != "mission_02_secure_the_woods_2":
            return False
        if state.turn != 2:
            return False
        if state.pending_decision.kind is not DecisionContextKind.CHOOSE_ORDER_PARAMETER:
            return False
        activation = state.current_activation
        if activation is None or activation.selected_die != 2:
            return False
        if tuple(order.value for order in activation.planned_orders) != ("advance", "scout"):
            return False
        if len(state.unresolved_markers) != 1 or "qm_1" not in state.unresolved_markers:
            return False
        if state.unresolved_markers["qm_1"].position != HexCoord(0, 0):
            return False
        if self._mission2_active_german(state) is not None:
            return False
        if any(unit.morale is BritishMorale.REMOVED for unit in state.british_units.values()):
            return False
        positions = {
            unit_id: (unit.position, unit.morale, unit.cover)
            for unit_id, unit in state.british_units.items()
        }
        return positions in (
            {
                "rifle_squad_a": (HexCoord(-1, 2), BritishMorale.NORMAL, 0),
                "rifle_squad_b": (HexCoord(0, 2), BritishMorale.NORMAL, 0),
            },
            {
                "rifle_squad_a": (HexCoord(0, 2), BritishMorale.NORMAL, 0),
                "rifle_squad_b": (HexCoord(-1, 2), BritishMorale.NORMAL, 0),
            },
        )

    def _is_mission2_turn2_left_scout_family(self, state: GameState) -> bool:
        if state.mission.mission_id != "mission_02_secure_the_woods_2":
            return False
        if state.turn != 2:
            return False
        if state.pending_decision.kind is not DecisionContextKind.CHOOSE_ORDER_PARAMETER:
            return False
        activation = state.current_activation
        if activation is None or activation.next_order_index != 1:
            return False
        if activation.selected_die != 2:
            return False
        if tuple(order.value for order in activation.planned_orders) != ("advance", "scout"):
            return False
        if len(state.unresolved_markers) != 1 or "qm_1" not in state.unresolved_markers:
            return False
        if state.unresolved_markers["qm_1"].position != HexCoord(0, 0):
            return False
        if any(unit.status is GermanUnitStatus.ACTIVE for unit in state.german_units.values()):
            return False
        if any(unit.morale is BritishMorale.REMOVED for unit in state.british_units.values()):
            return False
        active_unit = state.british_units[activation.active_unit_id]
        if active_unit.position != HexCoord(-1, 2):
            return False
        return active_unit.cover == 0

    def _is_mission2_late_left_scout_family(self, state: GameState) -> bool:
        if state.mission.mission_id != "mission_02_secure_the_woods_2":
            return False
        if state.turn < 3:
            return False
        if state.pending_decision.kind is not DecisionContextKind.CHOOSE_ORDER_PARAMETER:
            return False
        activation = state.current_activation
        if activation is None or activation.next_order_index != 1:
            return False
        if activation.selected_die != 2:
            return False
        active_unit = state.british_units[activation.active_unit_id]
        row = lookup_orders_chart_row(
            state.mission,
            unit_class=active_unit.unit_class,
            die_value=activation.selected_die,
        )
        if row.first_order is not OrderName.ADVANCE:
            return False
        if row.second_order is not OrderName.SCOUT:
            return False
        if len(state.unresolved_markers) != 1 or "qm_1" not in state.unresolved_markers:
            return False
        if state.unresolved_markers["qm_1"].position != HexCoord(0, 0):
            return False
        if any(unit.status is GermanUnitStatus.ACTIVE for unit in state.german_units.values()):
            return False
        if active_unit.position != HexCoord(-1, 2):
            return False
        return active_unit.cover == 0

    def _mission2_activation_die_key(self, state: GameState) -> str | None:
        if state.mission.mission_id != "mission_02_secure_the_woods_2":
            return None
        if state.pending_decision.kind is not DecisionContextKind.CHOOSE_ACTIVATION_DIE:
            return None
        activation = state.current_activation
        if activation is None:
            return None
        if state.turn > 2:
            return None
        active_germans = sum(
            1
            for unit in state.german_units.values()
            if unit.status is GermanUnitStatus.ACTIVE
        )
        if active_germans > 1 or len(state.unresolved_markers) > 1:
            return None
        british_bits = []
        for unit_id in sorted(state.british_units):
            unit = state.british_units[unit_id]
            british_bits.append(
                f"{unit_id}@({unit.position.q},{unit.position.r})/{unit.morale.value}/c{unit.cover}",
            )
        markers = sorted(
            f"{marker_id}@({marker.position.q},{marker.position.r})"
            for marker_id, marker in state.unresolved_markers.items()
        )
        roll = tuple(sorted(activation.roll))
        active_german = self._mission2_active_german(state)
        if active_german is None:
            active_german_text = "-"
        else:
            active_german_text = (
                f"{active_german.unit_class}@({active_german.position.q},{active_german.position.r})/"
                f"{active_german.facing.value}"
            )
        removed = sorted(
            (
                unit.unit_class,
                unit.position.q,
                unit.position.r,
            )
            for unit in state.german_units.values()
            if unit.status is GermanUnitStatus.REMOVED
        )
        removed_text = (
            "-"
            if not removed
            else ";".join(f"{unit_class}@({q},{r})" for unit_class, q, r in removed)
        )
        return (
            f"turn={state.turn}"
            f"|active={activation.active_unit_id}"
            f"|roll={roll}"
            f"|british={' ; '.join(british_bits)}"
            f"|active_german={active_german_text}"
            f"|removed={removed_text}"
            f"|markers={' ; '.join(markers) if markers else '-'}"
        )

    def _unit_priority_score(self, state: GameState, unit_id: str) -> float:
        score = super()._unit_priority_score(state, unit_id)
        if not self._mission1_single_active_unit_window(state):
            return score

        unit = state.british_units[unit_id]
        if unit.morale is BritishMorale.LOW:
            if (
                unit.position == HexCoord(0, 2)
                and self._active_fire_zone_count(unit.position, state) > 0
            ):
                score -= MISSION1_LOW_FORWARD_UNIT_PENALTY
            return score

        if unit.position == HexCoord(-1, 3):
            score += MISSION1_HEALTHY_RELAY_BONUS
        return score

    def _advance_score(self, state: GameState, action: AdvanceAction) -> float:
        score = super()._advance_score(state, action)

        active_unit = self._active_unit(state)
        active_units = self._active_german_units(state)
        reveal_count = len(movement_reveal_marker_ids(state, action.destination))
        if not active_units:
            if reveal_count == 0:
                score += self._staging_setup_bonus(
                    action.destination,
                    state,
                    active_unit_id=active_unit.unit_id,
                )
            else:
                continuation = self._expected_reveal_continuation_after_advance(state, action)
                score += 0.30 * continuation
                if (
                    len(state.unresolved_markers) == 1
                    and self._support_bonus(
                        action.destination,
                        state,
                        active_unit_id=active_unit.unit_id,
                    )
                    <= 0.0
                    and self._turn_pressure(state) < 0.90
                ):
                    score -= 18.0

        target = self._critical_single_active_target(state)
        if target is not None:
            destination = action.destination
            target_fire_zone = frozenset(german_fire_zone_hexes(state.mission, target))
            current_in_zone = active_unit.position in target_fire_zone
            destination_in_zone = destination in target_fire_zone
            adjacent = are_adjacent(destination, target.position)
            immediate_fire_prob = self._attack_probability(
                state,
                attacker_position=destination,
                attacker_cover=0,
                attack_order=OrderName.FIRE,
                target_unit_id=target.unit_id,
            )
            immediate_grenade_prob = self._attack_probability(
                state,
                attacker_position=destination,
                attacker_cover=0,
                attack_order=OrderName.GRENADE_ATTACK,
                target_unit_id=target.unit_id,
            )
            future_attack_prob = max(immediate_fire_prob, immediate_grenade_prob)

            if current_in_zone and not destination_in_zone:
                score += FLANK_FIRE_ZONE_ESCAPE_BONUS
            if adjacent:
                score += FLANK_FUTURE_ATTACK_BONUS * future_attack_prob
                if destination_in_zone:
                    score -= FLANK_IN_ZONE_ADJACENT_PENALTY
                    if active_unit.morale is BritishMorale.LOW:
                        score -= FLANK_LOW_MORALE_EXTRA_PENALTY
                    if not self._has_followup_attack(state):
                        score -= FLANK_NO_FOLLOWUP_IN_ZONE_PENALTY
                else:
                    score += FLANK_BONUS

        if self._is_mission1_opening_hidden_only(state) and active_unit.position == HexCoord(0, 3):
            destination = action.destination
            other_positions = {
                unit.position
                for unit_id, unit in state.british_units.items()
                if unit_id != active_unit.unit_id and unit.morale is not BritishMorale.REMOVED
            }
            if destination == HexCoord(-1, 3):
                score += MISSION1_LEFT_LANE_BONUS
                if HexCoord(1, 2) in other_positions:
                    score += 0.5 * MISSION1_LEFT_LANE_BONUS
            elif destination == HexCoord(0, 2):
                score -= MISSION1_CENTER_PENALTY
            elif destination == HexCoord(1, 2):
                if HexCoord(1, 2) in other_positions:
                    score -= MISSION1_STACK_RIGHT_PENALTY
                elif not self._opening_has_followup_scout(state):
                    score -= 0.35 * MISSION1_STACK_RIGHT_PENALTY

        if self._is_mission1_hidden_only(state):
            other_positions = self._other_live_positions(state, active_unit_id=active_unit.unit_id)
            if active_unit.position == HexCoord(0, 3) and HexCoord(-1, 3) in other_positions:
                if action.destination == HexCoord(1, 2):
                    score += MISSION1_SPLIT_RIGHT_BONUS
                elif action.destination == HexCoord(-1, 3):
                    score -= MISSION1_STACK_LEFT_PENALTY

        opening_table_key = self._mission1_opening_table_key(state)
        if opening_table_key is not None:
            destination_key = f"{action.destination.q},{action.destination.r}"
            table_bonus = MISSION1_OPENING_TABLE[opening_table_key].get(destination_key)
            if table_bonus is not None:
                score += MISSION1_OPENING_TABLE_SCALE * table_bonus

        if self._is_mission2_opening_mixed_b_anchor(state):
            activation = state.current_activation
            active_german = self._mission2_active_german(state)
            if activation is not None and active_german is not None:
                sorted_roll = tuple(sorted(activation.roll))
                row_signature = self._current_row_signature(state)
                if (
                    active_german.unit_class == "light_machine_gun"
                    and row_signature == "advance+scout"
                    and activation.selected_die == 2
                ):
                    if sorted_roll == (2, 2):
                        if action.destination == HexCoord(1, 2):
                            score += MISSION2_ROLL22_ONE_TWO_BONUS
                        elif action.destination == HexCoord(-1, 3):
                            score -= MISSION2_ROLL22_MINUS_ONE_THREE_PENALTY
                    elif sorted_roll == (2, 5):
                        if action.destination == HexCoord(0, 2):
                            score += MISSION2_ROLL25_ZERO_TWO_BONUS
                        elif action.destination == HexCoord(-1, 3):
                            score -= MISSION2_ROLL25_MINUS_ONE_THREE_PENALTY

        if self._is_mission2_turn2_advance_scout_family(state):
            activation = state.current_activation
            if activation is not None:
                if activation.active_unit_id in {"rifle_squad_a", "rifle_squad_b"}:
                    if action.destination == HexCoord(-1, 2):
                        score += MISSION2_TURN2_ADVANCE_BONUS
                    elif action.destination in {HexCoord(0, 1), HexCoord(1, 1)}:
                        score -= MISSION2_TURN2_ADVANCE_PENALTY

        return score

    def _scout_score(self, state: GameState, action: ScoutAction) -> float:
        score = super()._scout_score(state, action)

        if not self._active_german_units(state):
            continuation = self._expected_reveal_continuation_after_scout(state, action)
            score += 0.32 * continuation

        active_unit = self._active_unit(state)
        if self._is_mission1_opening_hidden_only(state) and active_unit.position == HexCoord(1, 2):
            if action.facing is HexDirection.DOWN_LEFT:
                score += MISSION1_RIGHT_LANE_DOWN_LEFT_SCOUT_BONUS
            elif action.facing is HexDirection.DOWN:
                score -= MISSION1_RIGHT_LANE_DOWN_SCOUT_PENALTY

        if self._is_mission1_hidden_only(state) and active_unit.position == HexCoord(-1, 3):
            if action.facing is HexDirection.DOWN_RIGHT:
                score += MISSION1_LEFT_SCOUT_DOWN_RIGHT_BONUS
            elif action.facing is HexDirection.DOWN:
                score -= MISSION1_LEFT_SCOUT_DOWN_PENALTY

        if self._is_mission2_turn2_advance_scout_family(state) and action.marker_id == "qm_1":
            if action.facing is HexDirection.DOWN_RIGHT:
                score += MISSION2_TURN2_SCOUT_BONUS
            elif action.facing in {HexDirection.DOWN, HexDirection.DOWN_LEFT}:
                score -= MISSION2_TURN2_SCOUT_PENALTY

        if self._is_mission2_turn2_left_scout_family(state) and action.marker_id == "qm_1":
            if action.facing is HexDirection.DOWN_RIGHT:
                score += MISSION2_TURN2_LEFT_DOWN_RIGHT_BONUS
            elif action.facing is HexDirection.DOWN:
                score -= MISSION2_TURN2_LEFT_DOWN_PENALTY
            elif action.facing is HexDirection.DOWN_LEFT:
                score -= MISSION2_TURN2_LEFT_DOWN_LEFT_PENALTY

        if self._is_mission2_late_left_scout_family(state) and action.marker_id == "qm_1":
            if action.facing is HexDirection.DOWN_RIGHT:
                score += MISSION2_LATE_LEFT_DOWN_RIGHT_BONUS
            elif action.facing is HexDirection.DOWN:
                score -= MISSION2_LATE_LEFT_DOWN_PENALTY
            elif action.facing is HexDirection.DOWN_LEFT:
                score -= MISSION2_LATE_LEFT_DOWN_LEFT_PENALTY

        return score

    def _staged_left_lane_hidden_exec_adjustment(
        self,
        state: GameState,
        action: ChooseOrderExecutionAction,
    ) -> float:
        if not self._is_mission1_hidden_only(state):
            return 0.0

        activation = state.current_activation
        if activation is None or activation.selected_die is None:
            return 0.0

        active_unit = self._active_unit(state)
        if active_unit.position != HexCoord(-1, 3):
            return 0.0

        row = lookup_orders_chart_row(
            state.mission,
            unit_class=active_unit.unit_class,
            die_value=activation.selected_die,
        )
        if row.first_order is not OrderName.ADVANCE or row.second_order is not OrderName.SCOUT:
            return 0.0

        current_staging = self._staging_setup_bonus(
            active_unit.position,
            state,
            active_unit_id=active_unit.unit_id,
        )
        destinations = self._legal_forward_destinations(active_unit.position, state)
        best_stage = max(
            (
                self._staging_setup_bonus(
                    destination,
                    state,
                    active_unit_id=active_unit.unit_id,
                )
                for destination in destinations
            ),
            default=current_staging,
        )
        if best_stage > current_staging + 0.5:
            return 0.0

        if action.choice is OrderExecutionChoice.SECOND_ORDER_ONLY:
            return MISSION1_SCOUT_ONLY_BONUS
        if action.choice is OrderExecutionChoice.BOTH_ORDERS:
            return -MISSION1_BOTH_ORDERS_PENALTY
        if action.choice is OrderExecutionChoice.FIRST_ORDER_ONLY:
            return -MISSION1_FIRST_ONLY_PENALTY
        return 0.0

    def _score_action(
        self,
        state: GameState,
        action: GameAction,
        *,
        depth: int,
    ) -> float:
        score = super()._score_action(state, action, depth=depth)
        target = self._critical_single_active_target(state)
        activation = state.current_activation

        if target is not None and activation is not None:
            urgency = self._endgame_urgency(state)

            if isinstance(action, SelectActivationDieAction):
                bonus = self._synthetic_endgame_choice_score(
                    state,
                    unit_id=activation.active_unit_id,
                    die_value=action.die_value,
                )
                score += ENDGAME_DIE_CHOICE_WEIGHT * bonus

            elif (
                isinstance(action, ChooseOrderExecutionAction)
                and activation.selected_die is not None
            ):
                row = lookup_orders_chart_row(
                    state.mission,
                    unit_class=self._active_unit(state).unit_class,
                    die_value=activation.selected_die,
                )
                plan_score = self._endgame_plan_score(
                    state,
                    planned_orders=self._planned_orders_for_choice(row, action.choice),
                )
                score += ENDGAME_ORDER_CHOICE_WEIGHT * plan_score

            elif isinstance(action, ResolveDoubleChoiceAction):
                active_unit_id = activation.active_unit_id
                if action.choice is DoubleChoiceOption.KEEP:
                    keep_score = self._synthetic_endgame_choice_score(
                        state,
                        unit_id=active_unit_id,
                        die_value=activation.roll[0],
                    )
                    score += ENDGAME_KEEP_CHOICE_WEIGHT * keep_score
                else:
                    reroll_total = 0.0
                    for die_value in range(1, 7):
                        reroll_total += self._synthetic_endgame_choice_score(
                            state,
                            unit_id=active_unit_id,
                            die_value=die_value,
                        )
                    score += ENDGAME_REROLL_CHOICE_WEIGHT * (reroll_total / 6.0)

            elif isinstance(action, DiscardActivationRollAction):
                best_available = max(
                    self._synthetic_endgame_choice_score(
                        state,
                        unit_id=activation.active_unit_id,
                        die_value=die_value,
                    )
                    for die_value in activation.roll
                )
                score -= urgency * (ENDGAME_DISCARD_PENALTY + best_available)

        if isinstance(action, ChooseOrderExecutionAction):
            score += self._staged_left_lane_hidden_exec_adjustment(state, action)

        if isinstance(action, ResolveDoubleChoiceAction):
            if self._mission1_hidden_double_window(state):
                if action.choice is DoubleChoiceOption.REROLL:
                    score += MISSION1_HIDDEN_REROLL_BONUS
                else:
                    score -= MISSION1_HIDDEN_KEEP_PENALTY

            table_scores = self._mission1_hidden_double_table_scores(state)
            if table_scores is not None:
                label = "reroll" if action.choice is DoubleChoiceOption.REROLL else "keep"
                table_bonus = table_scores.get(label)
                if table_bonus is not None:
                    score += MISSION1_HIDDEN_DOUBLE_TABLE_SCALE * table_bonus

        if isinstance(action, SelectActivationDieAction):
            if self._is_mission2_opening_mixed_b_anchor(state):
                active_german = self._mission2_active_german(state)
                if (
                    active_german is not None
                    and active_german.unit_class == "light_machine_gun"
                    and tuple(sorted(state.current_activation.roll)) == (3, 6)
                    and action.die_value == 6
                ):
                    score += MISSION2_LMG_DIE63_BONUS

            activation_key = self._mission2_activation_die_key(state)
            preferred_dice = None
            if activation_key is not None:
                preferred_dice = MISSION2_ACTIVATION_DIE_TABLE.get(activation_key)
            if preferred_dice is not None and action.die_value in preferred_dice:
                score += MISSION2_ACTIVATION_DIE_TABLE_BONUS

        return score


__all__ = ["ExactGuidedHeuristicAgent"]
