"""Mission-1-local exact fair-ceiling core with an explicit fair-agent contract.

Fair-agent contract for this exact Mission 1 reference:
- fair agents may use only player-visible information plus explicit rule knowledge
- fair agents may reason by expectation, exact chance expansion, or planner-local sampling
- fair agents may not peek at unrealized branch randomness, hidden runtime truth,
  or live ``rng_state`` as an oracle

This module is intentionally Mission-1-local and is not a generic planner/search
platform. The default module entrypoint mode is a bounded smoke probe so heavy
exact solving remains operator-owned.
"""

from __future__ import annotations

import argparse
import time
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, replace
from functools import lru_cache
from itertools import product
from pathlib import Path
from typing import Literal

import solo_wargame_ai.domain.legal_actions as legal_actions_module
from solo_wargame_ai.domain.actions import (
    AdvanceAction,
    ChooseOrderExecutionAction,
    DiscardActivationRollAction,
    FireAction,
    GameAction,
    GrenadeAttackAction,
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
    degrade_british_morale,
)
from solo_wargame_ai.domain.decision_context import (
    ChooseActivationDieContext,
    ChooseBritishUnitContext,
    ChooseDoubleChoiceContext,
    ChooseGermanUnitContext,
    ChooseOrderExecutionContext,
    ChooseOrderParameterContext,
)
from solo_wargame_ai.domain.german_fire import (
    calculate_german_fire_threshold,
    german_fire_target_ids,
    selectable_german_unit_ids,
)
from solo_wargame_ai.domain.legal_actions import get_legal_actions, lookup_orders_chart_row
from solo_wargame_ai.domain.mission import Mission, MissionObjectiveKind
from solo_wargame_ai.domain.reveal import facing_toward_adjacent_hex, movement_reveal_marker_ids
from solo_wargame_ai.domain.state import (
    CurrentActivation,
    GamePhase,
    GameState,
    TerminalOutcome,
    create_initial_game_state,
)
from solo_wargame_ai.domain.units import BritishMorale, GermanUnitStatus, RevealedGermanUnitState
from solo_wargame_ai.io import load_mission

MISSION1_DEFAULT_MISSION_PATH = Path("configs/missions/mission_01_secure_the_woods_1.toml")
SCRATCH_ESTIMATE_EVIDENCE_ONLY = 0.949848647767
MISSION1_FAIR_AGENT_CONTRACT: tuple[str, ...] = (
    "Use only player-visible information plus explicit rule knowledge.",
    "Reasoning may use expectation, exact chance expansion, or planner-local sampling.",
    "Do not peek at unrealized branch randomness, hidden runtime truth, or live rng_state.",
)
MISSION1_PRESERVED_ANCHORS: tuple[str, ...] = (
    "RandomAgent 11/200 floor",
    "learned best 144/200 observation-based learner reference",
    "HeuristicAgent 157/200 best current fair-ish historical baseline",
    "RolloutSearchAgent 195/200 preserved oracle/planner-like reference",
)

StateKey = tuple[object, ...]


@dataclass(frozen=True, slots=True)
class Mission1ChanceTableSummary:
    """Chance-table normalization summary for smoke/invariant checks."""

    activation_roll_probability_mass: float
    reveal_probability_mass: float


@dataclass(frozen=True, slots=True)
class Mission1ExactFairSmokeResult:
    """Short bounded proof that the tracked exact/fair path runs."""

    mission_id: str
    mode: Literal["smoke"]
    fair_agent_contract: tuple[str, ...]
    preserved_anchors: tuple[str, ...]
    scratch_estimate_evidence_only: float
    chance_tables: Mission1ChanceTableSummary
    root_action_count: int
    first_root_action: str
    first_root_action_outcome_mass: float
    solved_state_count: int


@dataclass(frozen=True, slots=True)
class Mission1ExactFairSolveResult:
    """Full exact Mission 1 fair-ceiling result."""

    mission_id: str
    mode: Literal["exact"]
    fair_agent_contract: tuple[str, ...]
    preserved_anchors: tuple[str, ...]
    scratch_estimate_evidence_only: float
    fair_ceiling: float
    root_action_values: tuple[tuple[str, float], ...]
    solved_state_count: int


@dataclass(frozen=True, slots=True)
class _Mission1ExactFairSolver:
    """Mission-1-local exact/fair solver internals."""

    mission: Mission
    chance_tables: Mission1ChanceTableSummary
    intern_state: Callable[[GameState], StateKey]
    representative_state: Callable[[StateKey], GameState]
    legal_actions_for: Callable[[StateKey], tuple[GameAction, ...]]
    value: Callable[[StateKey], float]
    action_value: Callable[[StateKey, GameAction], float]
    action_outcome_mass: Callable[[StateKey, GameAction], float]
    maybe_report_progress: Callable[[bool], None]
    solved_state_count: Callable[[], int]

    def root_state_key(self, *, seed: int) -> StateKey:
        return self.intern_state(create_initial_game_state(self.mission, seed=seed))


def _build_mission1_exact_fair_solver(
    mission: Mission,
    *,
    progress_interval_sec: float,
) -> _Mission1ExactFairSolver:
    if mission.objective.kind is not MissionObjectiveKind.CLEAR_ALL_HOSTILES:
        raise ValueError("Mission 1 exact fair ceiling supports only clear_all_hostiles")

    roll_probs: Counter[tuple[int, int]] = Counter()
    for first_die in range(1, 7):
        for second_die in range(1, 7):
            roll_probs[tuple(sorted((first_die, second_die)))] += 1.0 / 36.0

    two_d6_hit_counts = {
        threshold: sum(
            1
            for first_die in range(1, 7)
            for second_die in range(1, 7)
            if first_die + second_die >= threshold
        )
        for threshold in range(-20, 40)
    }

    reveal_probs: Counter[str] = Counter()
    for row in mission.german.reveal_table:
        reveal_probs[row.result_unit_class] += (row.roll_max - row.roll_min + 1) / 6.0

    chance_tables = Mission1ChanceTableSummary(
        activation_roll_probability_mass=sum(roll_probs.values()),
        reveal_probability_mass=sum(reveal_probs.values()),
    )

    representative_states: dict[StateKey, GameState] = {}
    start_time = time.monotonic()
    last_progress = start_time
    last_progress_state_count = 0
    solved_by_kind: Counter[str] = Counter()

    def maybe_report_progress(force: bool = False) -> None:
        nonlocal last_progress, last_progress_state_count
        now = time.monotonic()
        state_count = len(representative_states)
        if not force and now - last_progress < progress_interval_sec:
            return
        if not force and state_count == last_progress_state_count:
            return
        elapsed = now - start_time
        value_cache_info = value.cache_info()
        action_value_cache_info = action_value.cache_info()
        print(
            "[progress] "
            f"elapsed={elapsed:.1f}s "
            f"states={state_count} "
            f"V(hits={value_cache_info.hits}, misses={value_cache_info.misses}, "
            f"currsize={value_cache_info.currsize}) "
            f"Q(hits={action_value_cache_info.hits}, misses={action_value_cache_info.misses}, "
            f"currsize={action_value_cache_info.currsize}) "
            f"solved={dict(solved_by_kind)}",
            flush=True,
        )
        last_progress = now
        last_progress_state_count = state_count

    def canonical_roll(roll: tuple[int, int] | None) -> tuple[int, int] | None:
        if roll is None:
            return None
        return tuple(sorted(roll))

    def pending_extra(pending_decision) -> tuple[str, int] | None:
        if isinstance(pending_decision, ChooseOrderParameterContext):
            return (pending_decision.order.value, int(pending_decision.order_index))
        return None

    def state_key(state: GameState) -> StateKey:
        activation = state.current_activation
        return (
            int(state.turn),
            state.phase.value,
            state.pending_decision.kind.value,
            pending_extra(state.pending_decision),
            None if state.terminal_outcome is None else state.terminal_outcome.value,
            tuple(sorted(state.activated_british_unit_ids)),
            tuple(sorted(state.activated_german_unit_ids)),
            None
            if activation is None
            else (
                activation.active_unit_id,
                canonical_roll(activation.roll),
                activation.selected_die,
                tuple(order.value for order in activation.planned_orders),
                int(activation.next_order_index),
            ),
            tuple(
                sorted(
                    (
                        unit.unit_id,
                        unit.position.q,
                        unit.position.r,
                        unit.morale.value,
                        int(unit.cover),
                    )
                    for unit in state.british_units.values()
                )
            ),
            tuple(
                sorted(
                    (
                        unit.unit_id,
                        unit.unit_class,
                        unit.facing.value,
                        unit.status.value,
                    )
                    for unit in state.german_units.values()
                )
            ),
            tuple(sorted(state.unresolved_markers)),
        )

    def is_victory_state(state: GameState) -> bool:
        return not state.unresolved_markers and not any(
            unit.status is GermanUnitStatus.ACTIVE for unit in state.german_units.values()
        )

    def selectable_british_ids(state: GameState) -> tuple[str, ...]:
        return legal_actions_module._selectable_british_unit_ids(
            state,
            activated_british_unit_ids=state.activated_british_unit_ids,
        )

    def auto_progress(state: GameState) -> GameState:
        progressed = state
        while progressed.terminal_outcome is None:
            if is_victory_state(progressed):
                pending = (
                    ChooseGermanUnitContext()
                    if progressed.phase is GamePhase.GERMAN
                    else ChooseBritishUnitContext()
                )
                progressed = replace(
                    progressed,
                    pending_decision=pending,
                    current_activation=None,
                    terminal_outcome=TerminalOutcome.VICTORY,
                )
                break

            if (
                progressed.phase is GamePhase.GERMAN
                and not selectable_german_unit_ids(progressed)
                and progressed.turn >= progressed.mission.turns.turn_limit
            ):
                progressed = replace(
                    progressed,
                    pending_decision=ChooseGermanUnitContext(),
                    current_activation=None,
                    terminal_outcome=TerminalOutcome.DEFEAT,
                )
                break

            if (
                progressed.phase is GamePhase.BRITISH
                and isinstance(progressed.pending_decision, ChooseBritishUnitContext)
                and progressed.current_activation is None
                and not selectable_british_ids(progressed)
            ):
                progressed = replace(
                    progressed,
                    phase=GamePhase.GERMAN,
                    activated_german_unit_ids=frozenset(),
                    pending_decision=ChooseGermanUnitContext(),
                    current_activation=None,
                )
                continue

            if progressed.phase is GamePhase.GERMAN and not selectable_german_unit_ids(progressed):
                progressed = replace(
                    progressed,
                    turn=progressed.turn + 1,
                    phase=GamePhase.BRITISH,
                    activated_british_unit_ids=frozenset(),
                    activated_german_unit_ids=frozenset(),
                    pending_decision=ChooseBritishUnitContext(),
                    current_activation=None,
                )
                continue

            break

        return progressed

    def intern_state(state: GameState) -> StateKey:
        progressed = auto_progress(state)
        key = state_key(progressed)
        if key not in representative_states:
            representative_states[key] = progressed
            maybe_report_progress()
        return key

    def representative_state(key: StateKey) -> GameState:
        return representative_states[key]

    def hit_probability(threshold: int) -> float:
        return two_d6_hit_counts.get(threshold, 0) / 36.0

    @lru_cache(maxsize=None)
    def legal_actions_for(key: StateKey) -> tuple[GameAction, ...]:
        return get_legal_actions(representative_state(key))

    def finish_activation(state: GameState) -> GameState:
        activation = state.current_activation
        if activation is None:
            raise AssertionError("finish_activation requires current_activation")
        activated_unit_ids = frozenset(
            (*state.activated_british_unit_ids, activation.active_unit_id),
        )
        remaining_units = legal_actions_module._selectable_british_unit_ids(
            state,
            activated_british_unit_ids=activated_unit_ids,
        )
        if remaining_units:
            return replace(
                state,
                activated_british_unit_ids=activated_unit_ids,
                pending_decision=ChooseBritishUnitContext(),
                current_activation=None,
            )
        return replace(
            state,
            phase=GamePhase.GERMAN,
            activated_british_unit_ids=activated_unit_ids,
            activated_german_unit_ids=frozenset(),
            pending_decision=ChooseGermanUnitContext(),
            current_activation=None,
        )

    def deterministic_next_states(state: GameState, action: GameAction) -> Counter[StateKey]:
        if isinstance(action, SelectActivationDieAction):
            next_state = replace(
                state,
                pending_decision=ChooseOrderExecutionContext(),
                current_activation=replace(state.current_activation, selected_die=action.die_value),
            )
        elif isinstance(action, DiscardActivationRollAction):
            next_state = finish_activation(state)
        elif isinstance(action, ChooseOrderExecutionAction):
            activation = state.current_activation
            if activation is None:
                raise AssertionError("ChooseOrderExecutionAction requires current_activation")
            active_unit = state.british_units[activation.active_unit_id]
            orders_row = lookup_orders_chart_row(
                state.mission,
                unit_class=active_unit.unit_class,
                die_value=activation.selected_die or 0,
            )
            if action.choice.value == "no_action":
                next_state = finish_activation(state)
            else:
                if action.choice.value == "first_order_only":
                    planned_orders = (orders_row.first_order,)
                elif action.choice.value == "second_order_only":
                    planned_orders = (orders_row.second_order,)
                else:
                    planned_orders = (orders_row.first_order, orders_row.second_order)
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
        elif isinstance(action, TakeCoverAction):
            activation = state.current_activation
            if activation is None:
                raise AssertionError("TakeCoverAction requires current_activation")
            active_unit = state.british_units[activation.active_unit_id]
            british_units = dict(state.british_units)
            british_units[active_unit.unit_id] = replace(active_unit, cover=active_unit.cover + 1)
            next_state = legal_actions_module._continue_after_resolved_order(
                state,
                british_units=british_units,
                german_units=state.german_units,
                unresolved_markers=state.unresolved_markers,
                rng_state=state.rng_state,
            )
        elif isinstance(action, RallyAction):
            activation = state.current_activation
            if activation is None:
                raise AssertionError("RallyAction requires current_activation")
            active_unit = state.british_units[activation.active_unit_id]
            british_units = dict(state.british_units)
            british_units[active_unit.unit_id] = replace(
                active_unit,
                morale=(
                    BritishMorale.NORMAL
                    if active_unit.morale is BritishMorale.LOW
                    else active_unit.morale
                ),
            )
            next_state = legal_actions_module._continue_after_resolved_order(
                state,
                british_units=british_units,
                german_units=state.german_units,
                unresolved_markers=state.unresolved_markers,
                rng_state=state.rng_state,
            )
        else:
            raise AssertionError(f"Unsupported deterministic action: {type(action)!r}")
        return Counter({intern_state(next_state): 1.0})

    def expand_select_british(
        state: GameState,
        action: SelectBritishUnitAction,
    ) -> Counter[StateKey]:
        outcomes: Counter[StateKey] = Counter()
        for roll, probability in roll_probs.items():
            pending = (
                ChooseDoubleChoiceContext()
                if roll[0] == roll[1]
                else ChooseActivationDieContext()
            )
            next_state = replace(
                state,
                pending_decision=pending,
                current_activation=CurrentActivation(active_unit_id=action.unit_id, roll=roll),
            )
            outcomes[intern_state(next_state)] += probability
        return outcomes

    def keep_state_with_double(state: GameState, *, double_value: int) -> StateKey:
        activation = state.current_activation
        if activation is None:
            raise AssertionError("double keep requires current_activation")
        next_state = replace(
            state,
            pending_decision=ChooseActivationDieContext(),
            current_activation=replace(
                activation,
                roll=(double_value, double_value),
                selected_die=None,
                planned_orders=(),
                next_order_index=0,
            ),
        )
        return intern_state(next_state)

    def expand_advance(state: GameState, action: AdvanceAction) -> Counter[StateKey]:
        activation = state.current_activation
        if activation is None:
            raise AssertionError("Advance requires current_activation")
        active_unit = state.british_units[activation.active_unit_id]
        british_units = dict(state.british_units)
        british_units[active_unit.unit_id] = replace(
            active_unit,
            position=action.destination,
            cover=0,
        )

        marker_ids = movement_reveal_marker_ids(state, action.destination)
        if not marker_ids:
            next_state = legal_actions_module._continue_after_resolved_order(
                state,
                british_units=british_units,
                german_units=state.german_units,
                unresolved_markers=state.unresolved_markers,
                rng_state=state.rng_state,
            )
            return Counter({intern_state(next_state): 1.0})

        if len(marker_ids) != 1:
            raise AssertionError(
                f"Mission 1 exact solver expected one reveal marker, got {marker_ids!r}",
            )

        marker_id = marker_ids[0]
        marker_state = state.unresolved_markers[marker_id]
        facing = facing_toward_adjacent_hex(marker_state.position, action.destination)
        unresolved_markers = dict(state.unresolved_markers)
        unresolved_markers.pop(marker_id)

        outcomes: Counter[StateKey] = Counter()
        for unit_class, probability in reveal_probs.items():
            german_units = dict(state.german_units)
            german_units[marker_id] = RevealedGermanUnitState(
                unit_id=marker_id,
                unit_class=unit_class,
                position=marker_state.position,
                facing=facing,
                status=GermanUnitStatus.ACTIVE,
            )
            next_state = legal_actions_module._continue_after_resolved_order(
                state,
                british_units=british_units,
                german_units=german_units,
                unresolved_markers=unresolved_markers,
                rng_state=state.rng_state,
            )
            outcomes[intern_state(next_state)] += probability
        return outcomes

    def expand_scout(state: GameState, action: ScoutAction) -> Counter[StateKey]:
        marker_state = state.unresolved_markers[action.marker_id]
        unresolved_markers = dict(state.unresolved_markers)
        unresolved_markers.pop(action.marker_id)
        outcomes: Counter[StateKey] = Counter()
        for unit_class, probability in reveal_probs.items():
            german_units = dict(state.german_units)
            german_units[action.marker_id] = RevealedGermanUnitState(
                unit_id=action.marker_id,
                unit_class=unit_class,
                position=marker_state.position,
                facing=action.facing,
                status=GermanUnitStatus.ACTIVE,
            )
            next_state = legal_actions_module._continue_after_resolved_order(
                state,
                british_units=state.british_units,
                german_units=german_units,
                unresolved_markers=unresolved_markers,
                rng_state=state.rng_state,
            )
            outcomes[intern_state(next_state)] += probability
        return outcomes

    def expand_attack(
        state: GameState,
        action: FireAction | GrenadeAttackAction,
    ) -> Counter[StateKey]:
        activation = state.current_activation
        if activation is None:
            raise AssertionError("attack requires current_activation")
        attacker = state.british_units[activation.active_unit_id]
        defender = state.german_units[action.target_unit_id]
        threshold = (
            calculate_fire_threshold(
                mission,
                attacker=attacker,
                defender=defender,
                british_units=state.british_units,
            )
            if isinstance(action, FireAction)
            else calculate_grenade_attack_threshold(mission, attacker=attacker)
        )
        probability_hit = hit_probability(threshold)
        outcomes: Counter[StateKey] = Counter()
        for did_hit, probability in ((False, 1.0 - probability_hit), (True, probability_hit)):
            if probability <= 0.0:
                continue
            german_units = dict(state.german_units)
            if did_hit:
                german_units[action.target_unit_id] = replace(
                    defender,
                    status=GermanUnitStatus.REMOVED,
                )
            next_state = legal_actions_module._continue_after_resolved_order(
                state,
                british_units=state.british_units,
                german_units=german_units,
                unresolved_markers=state.unresolved_markers,
                rng_state=state.rng_state,
            )
            outcomes[intern_state(next_state)] += probability
        return outcomes

    def expand_select_german(state: GameState, action: SelectGermanUnitAction) -> Counter[StateKey]:
        target_ids = german_fire_target_ids(state, attacker_unit_id=action.unit_id)
        if not target_ids:
            next_state = replace(
                state,
                activated_german_unit_ids=frozenset(
                    (*state.activated_german_unit_ids, action.unit_id),
                ),
                pending_decision=ChooseGermanUnitContext(),
                current_activation=None,
            )
            return Counter({intern_state(next_state): 1.0})

        target_hit_probabilities = {
            target_id: hit_probability(
                calculate_german_fire_threshold(
                    state,
                    attacker_unit_id=action.unit_id,
                    target_unit_id=target_id,
                )
            )
            for target_id in target_ids
        }

        outcomes: Counter[StateKey] = Counter()
        for hit_vector in product([False, True], repeat=len(target_ids)):
            probability = 1.0
            british_units = dict(state.british_units)
            for target_id, did_hit in zip(target_ids, hit_vector, strict=True):
                hit_probability_value = target_hit_probabilities[target_id]
                probability *= hit_probability_value if did_hit else (1.0 - hit_probability_value)
                if did_hit:
                    target = british_units[target_id]
                    british_units[target_id] = replace(
                        target,
                        morale=degrade_british_morale(target.morale),
                    )
            if probability <= 0.0:
                continue
            next_state = replace(
                state,
                british_units=british_units,
                activated_german_unit_ids=frozenset(
                    (*state.activated_german_unit_ids, action.unit_id),
                ),
                pending_decision=ChooseGermanUnitContext(),
                current_activation=None,
            )
            outcomes[intern_state(next_state)] += probability
        return outcomes

    def reroll_value(state: GameState) -> float:
        keep_values = [
            value(keep_state_with_double(state, double_value=die_value))
            for die_value in range(1, 7)
        ]
        non_double_total = 0.0
        for roll, probability in roll_probs.items():
            if roll[0] == roll[1]:
                continue
            next_state = replace(
                state,
                pending_decision=ChooseActivationDieContext(),
                current_activation=replace(
                    state.current_activation,
                    roll=roll,
                    selected_die=None,
                    planned_orders=(),
                    next_order_index=0,
                ),
            )
            non_double_total += probability * value(intern_state(next_state))

        sorted_keep_values = sorted(keep_values)
        for split_index in range(7):
            candidate = (
                non_double_total + sum(sorted_keep_values[split_index:]) / 36.0
            ) / (1.0 - split_index / 36.0)
            lower_ok = split_index == 0 or sorted_keep_values[split_index - 1] <= candidate + 1e-15
            upper_ok = split_index == 6 or candidate <= sorted_keep_values[split_index] + 1e-15
            if lower_ok and upper_ok:
                return candidate
        raise AssertionError("failed to solve reroll fixed point")

    def expanded_action_outcomes(state: GameState, action: GameAction) -> Counter[StateKey]:
        if isinstance(action, SelectBritishUnitAction):
            return expand_select_british(state, action)
        if isinstance(action, AdvanceAction):
            return expand_advance(state, action)
        if isinstance(action, ScoutAction):
            return expand_scout(state, action)
        if isinstance(action, FireAction | GrenadeAttackAction):
            return expand_attack(state, action)
        if isinstance(action, SelectGermanUnitAction):
            return expand_select_german(state, action)
        if isinstance(action, ResolveDoubleChoiceAction):
            if action.choice.value == "keep":
                keep_key = keep_state_with_double(
                    state,
                    double_value=state.current_activation.roll[0],
                )
                return Counter({keep_key: 1.0})
            return Counter()
        return deterministic_next_states(state, action)

    def action_outcome_mass(key: StateKey, action: GameAction) -> float:
        state = representative_state(key)
        if isinstance(action, ResolveDoubleChoiceAction) and action.choice.value == "reroll":
            return 1.0
        return float(sum(expanded_action_outcomes(state, action).values()))

    @lru_cache(maxsize=None)
    def value(key: StateKey) -> float:
        state = representative_state(key)
        solved_by_kind[state.pending_decision.kind.value] += 1
        if state.terminal_outcome is TerminalOutcome.VICTORY:
            return 1.0
        if state.terminal_outcome is TerminalOutcome.DEFEAT:
            return 0.0

        if isinstance(state.pending_decision, ChooseDoubleChoiceContext):
            double_value = state.current_activation.roll[0]
            return max(
                value(keep_state_with_double(state, double_value=double_value)),
                reroll_value(state),
            )

        best_value = -1.0
        for action in legal_actions_for(key):
            q_value = action_value(key, action)
            if q_value > best_value:
                best_value = q_value
        return best_value

    @lru_cache(maxsize=None)
    def action_value(key: StateKey, action: GameAction) -> float:
        state = representative_state(key)
        if isinstance(action, ResolveDoubleChoiceAction) and action.choice.value == "reroll":
            return reroll_value(state)
        outcomes = expanded_action_outcomes(state, action)
        total = 0.0
        for next_key, probability in outcomes.items():
            total += probability * value(next_key)
        return total

    return _Mission1ExactFairSolver(
        mission=mission,
        chance_tables=chance_tables,
        intern_state=intern_state,
        representative_state=representative_state,
        legal_actions_for=legal_actions_for,
        value=value,
        action_value=action_value,
        action_outcome_mass=action_outcome_mass,
        maybe_report_progress=maybe_report_progress,
        solved_state_count=lambda: len(representative_states),
    )


def run_mission1_exact_fair_smoke(
    mission: Mission,
    *,
    seed: int = 0,
    progress_interval_sec: float = 60.0,
) -> Mission1ExactFairSmokeResult:
    """Run a short bounded smoke probe for the tracked exact/fair core."""

    solver = _build_mission1_exact_fair_solver(
        mission,
        progress_interval_sec=progress_interval_sec,
    )
    root_key = solver.root_state_key(seed=seed)
    root_actions = solver.legal_actions_for(root_key)
    if not root_actions:
        raise RuntimeError("Expected at least one legal root action for smoke probe")

    first_action = root_actions[0]
    first_action_outcome_mass = solver.action_outcome_mass(root_key, first_action)

    return Mission1ExactFairSmokeResult(
        mission_id=mission.mission_id,
        mode="smoke",
        fair_agent_contract=MISSION1_FAIR_AGENT_CONTRACT,
        preserved_anchors=MISSION1_PRESERVED_ANCHORS,
        scratch_estimate_evidence_only=SCRATCH_ESTIMATE_EVIDENCE_ONLY,
        chance_tables=solver.chance_tables,
        root_action_count=len(root_actions),
        first_root_action=repr(first_action),
        first_root_action_outcome_mass=first_action_outcome_mass,
        solved_state_count=solver.solved_state_count(),
    )


def solve_mission1_exact_fair_ceiling(
    mission: Mission,
    *,
    seed: int = 0,
    progress_interval_sec: float = 5.0,
) -> Mission1ExactFairSolveResult:
    """Run the full exact Mission 1 fair-ceiling solve."""

    solver = _build_mission1_exact_fair_solver(
        mission,
        progress_interval_sec=progress_interval_sec,
    )
    root_key = solver.root_state_key(seed=seed)
    fair_ceiling = solver.value(root_key)
    solver.maybe_report_progress(force=True)

    root_action_values = tuple(
        sorted(
            (
                (repr(action), solver.action_value(root_key, action))
                for action in solver.legal_actions_for(root_key)
            ),
            key=lambda item: (-item[1], item[0]),
        ),
    )

    return Mission1ExactFairSolveResult(
        mission_id=mission.mission_id,
        mode="exact",
        fair_agent_contract=MISSION1_FAIR_AGENT_CONTRACT,
        preserved_anchors=MISSION1_PRESERVED_ANCHORS,
        scratch_estimate_evidence_only=SCRATCH_ESTIMATE_EVIDENCE_ONLY,
        fair_ceiling=fair_ceiling,
        root_action_values=root_action_values,
        solved_state_count=solver.solved_state_count(),
    )


def _format_smoke_result(result: Mission1ExactFairSmokeResult) -> str:
    lines = [
        "=== Mission 1 Exact Fair Ceiling Smoke ===",
        f"mission_id: {result.mission_id}",
        "mode: smoke",
        f"root_action_count: {result.root_action_count}",
        f"first_root_action: {result.first_root_action}",
        f"first_root_action_outcome_mass: {result.first_root_action_outcome_mass:.12f}",
        (
            "activation_roll_probability_mass: "
            f"{result.chance_tables.activation_roll_probability_mass:.12f}"
        ),
        f"reveal_probability_mass: {result.chance_tables.reveal_probability_mass:.12f}",
        f"interned_states: {result.solved_state_count}",
        "fair_agent_contract:",
    ]
    lines.extend(f"  - {line}" for line in result.fair_agent_contract)
    lines.extend(
        [
            "preserved_anchors:",
            *[f"  - {anchor}" for anchor in result.preserved_anchors],
            (
                "scratch_estimate_evidence_only: "
                f"{result.scratch_estimate_evidence_only:.12f}"
            ),
            "scratch_estimate_status: evidence-only (not accepted reference)",
        ],
    )
    return "\n".join(lines)


def _format_exact_result(result: Mission1ExactFairSolveResult) -> str:
    lines = [
        "=== Mission 1 Exact Fair Ceiling ===",
        f"mission_id: {result.mission_id}",
        "mode: exact",
        f"fair_ceiling: {result.fair_ceiling:.12f}",
        f"interned_states: {result.solved_state_count}",
        "fair_agent_contract:",
    ]
    lines.extend(f"  - {line}" for line in result.fair_agent_contract)
    lines.extend(
        [
            "preserved_anchors:",
            *[f"  - {anchor}" for anchor in result.preserved_anchors],
            (
                "scratch_estimate_evidence_only: "
                f"{result.scratch_estimate_evidence_only:.12f}"
            ),
            "scratch_estimate_status: evidence-only (not accepted reference)",
            "root_actions:",
        ],
    )
    lines.extend(f"  {action}: {value:.12f}" for action, value in result.root_action_values)
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Mission-1-local exact fair-ceiling workflow.",
    )
    parser.add_argument(
        "--mode",
        choices=("smoke", "exact"),
        default="smoke",
        help="Use smoke for a short bounded probe; exact for the full solve.",
    )
    parser.add_argument(
        "--mission",
        default=str(MISSION1_DEFAULT_MISSION_PATH),
        help="Path to Mission 1 TOML. Defaults to the tracked Mission 1 config.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Initial RNG seed used for root state construction.",
    )
    parser.add_argument(
        "--progress-interval-sec",
        type=float,
        default=5.0,
        help="Progress print interval for exact mode; smoke remains bounded.",
    )
    args = parser.parse_args()

    mission = load_mission(Path(args.mission))
    if args.mode == "smoke":
        result = run_mission1_exact_fair_smoke(
            mission,
            seed=args.seed,
            progress_interval_sec=max(args.progress_interval_sec, 30.0),
        )
        print(_format_smoke_result(result), flush=True)
        return

    result = solve_mission1_exact_fair_ceiling(
        mission,
        seed=args.seed,
        progress_interval_sec=args.progress_interval_sec,
    )
    print(_format_exact_result(result), flush=True)


if __name__ == "__main__":
    main()


__all__ = [
    "MISSION1_DEFAULT_MISSION_PATH",
    "MISSION1_FAIR_AGENT_CONTRACT",
    "MISSION1_PRESERVED_ANCHORS",
    "SCRATCH_ESTIMATE_EVIDENCE_ONLY",
    "Mission1ChanceTableSummary",
    "Mission1ExactFairSmokeResult",
    "Mission1ExactFairSolveResult",
    "run_mission1_exact_fair_smoke",
    "solve_mission1_exact_fair_ceiling",
]
