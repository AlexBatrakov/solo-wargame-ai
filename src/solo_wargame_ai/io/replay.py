"""Stage 7 replay and trace helpers layered over the accepted resolver path."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Sequence

from solo_wargame_ai.domain.actions import (
    AdvanceAction,
    ChooseOrderExecutionAction,
    DiscardActivationRollAction,
    DoubleChoiceOption,
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
)
from solo_wargame_ai.domain.german_fire import (
    calculate_german_fire_threshold,
    german_fire_target_ids,
)
from solo_wargame_ai.domain.hexgrid import HexCoord
from solo_wargame_ai.domain.mission import Mission
from solo_wargame_ai.domain.resolver import (
    apply_action,
    get_legal_actions,
    resolve_automatic_progression,
)
from solo_wargame_ai.domain.reveal import movement_reveal_marker_ids
from solo_wargame_ai.domain.rng import DeterministicRNG, RNGState
from solo_wargame_ai.domain.state import (
    CurrentActivation,
    GameState,
    create_initial_game_state,
)
from solo_wargame_ai.domain.units import BritishMorale, GermanUnitStatus


class ReplayEventKind(StrEnum):
    """Structured replay event kinds emitted by the Stage 7 adapter."""

    ACTION_SELECTED = "action_selected"
    RANDOM_DRAW = "random_draw"
    REVEAL_RESOLVED = "reveal_resolved"
    ATTACK_RESOLVED = "attack_resolved"
    MORALE_CHANGED = "morale_changed"
    UNIT_REMOVED = "unit_removed"
    PHASE_ADVANCED = "phase_advanced"
    TURN_ADVANCED = "turn_advanced"
    TERMINAL_OUTCOME_SET = "terminal_outcome_set"


class ReplayConsistencyError(RuntimeError):
    """Raised when a recorded replay no longer matches resolver behavior."""


@dataclass(frozen=True, slots=True)
class ReplayEvent:
    """One structured replay event derived from the accepted engine path."""

    kind: ReplayEventKind
    details: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind.value,
            "details": _serialize_value(self.details),
        }


@dataclass(frozen=True, slots=True)
class ReplayActivationSummary:
    """Stable snapshot of the in-progress British activation state."""

    active_unit_id: str
    roll: tuple[int, int] | None
    selected_die: int | None
    planned_orders: tuple[str, ...]
    next_order_index: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "active_unit_id": self.active_unit_id,
            "roll": None if self.roll is None else list(self.roll),
            "selected_die": self.selected_die,
            "planned_orders": list(self.planned_orders),
            "next_order_index": self.next_order_index,
        }


@dataclass(frozen=True, slots=True)
class ReplayBritishUnitSummary:
    """Stable summary of one British unit."""

    unit_id: str
    unit_class: str
    position: tuple[int, int]
    morale: str
    cover: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "unit_id": self.unit_id,
            "unit_class": self.unit_class,
            "position": _coord_dict(self.position),
            "morale": self.morale,
            "cover": self.cover,
        }


@dataclass(frozen=True, slots=True)
class ReplayGermanUnitSummary:
    """Stable summary of one revealed German unit."""

    unit_id: str
    unit_class: str
    position: tuple[int, int]
    facing: str
    status: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "unit_id": self.unit_id,
            "unit_class": self.unit_class,
            "position": _coord_dict(self.position),
            "facing": self.facing,
            "status": self.status,
        }


@dataclass(frozen=True, slots=True)
class ReplayMarkerSummary:
    """Stable summary of one unresolved hidden marker."""

    marker_id: str
    position: tuple[int, int]

    def to_dict(self) -> dict[str, Any]:
        return {
            "marker_id": self.marker_id,
            "position": _coord_dict(self.position),
        }


@dataclass(frozen=True, slots=True)
class ReplayStateSummary:
    """Deterministic state summary used for trace comparison and reporting."""

    turn: int
    phase: str
    pending_decision: str
    terminal_outcome: str | None
    activated_british_unit_ids: tuple[str, ...]
    activated_german_unit_ids: tuple[str, ...]
    current_activation: ReplayActivationSummary | None
    british_units: tuple[ReplayBritishUnitSummary, ...]
    german_units: tuple[ReplayGermanUnitSummary, ...]
    unresolved_markers: tuple[ReplayMarkerSummary, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "turn": self.turn,
            "phase": self.phase,
            "pending_decision": self.pending_decision,
            "terminal_outcome": self.terminal_outcome,
            "activated_british_unit_ids": list(self.activated_british_unit_ids),
            "activated_german_unit_ids": list(self.activated_german_unit_ids),
            "current_activation": (
                None if self.current_activation is None else self.current_activation.to_dict()
            ),
            "british_units": [unit.to_dict() for unit in self.british_units],
            "german_units": [unit.to_dict() for unit in self.german_units],
            "unresolved_markers": [marker.to_dict() for marker in self.unresolved_markers],
        }


@dataclass(frozen=True, slots=True)
class ReplayStep:
    """One player-selected action plus derived deterministic replay records."""

    index: int
    before: ReplayStateSummary
    action: GameAction
    events: tuple[ReplayEvent, ...]
    after: ReplayStateSummary

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "before": self.before.to_dict(),
            "action": serialize_action(self.action),
            "events": [event.to_dict() for event in self.events],
            "after": self.after.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class ReplayTrace:
    """Structured deterministic trace for a fixed mission, seed, and actions."""

    mission_id: str
    initial_seed: int | None
    initial_rng_state: RNGState
    initial_state: ReplayStateSummary
    steps: tuple[ReplayStep, ...]
    final_state: ReplayStateSummary

    @property
    def actions(self) -> tuple[GameAction, ...]:
        return tuple(step.action for step in self.steps)

    def to_dict(self) -> dict[str, Any]:
        return {
            "mission_id": self.mission_id,
            "initial_seed": self.initial_seed,
            "initial_rng_state": self.initial_rng_state.to_dict(),
            "initial_state": self.initial_state.to_dict(),
            "steps": [step.to_dict() for step in self.steps],
            "final_state": self.final_state.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class ReplayRunResult:
    """Result of executing a fixed action sequence through the replay adapter."""

    final_state: GameState
    trace: ReplayTrace


@dataclass(frozen=True, slots=True)
class _PredictedRandomDraw:
    purpose: str
    values: tuple[int, ...]
    details: dict[str, Any]

    def to_event(self) -> ReplayEvent:
        return ReplayEvent(
            kind=ReplayEventKind.RANDOM_DRAW,
            details={
                "purpose": self.purpose,
                "values": list(self.values),
                **self.details,
            },
        )


def run_action_replay(
    mission: Mission,
    *,
    seed: int | None,
    actions: Sequence[GameAction],
) -> ReplayRunResult:
    """Run a fixed action sequence through the accepted playable resolver path."""

    state = resolve_automatic_progression(create_initial_game_state(mission, seed=seed))
    initial_rng_state = state.rng_state
    initial_state = summarize_state(state)
    steps: list[ReplayStep] = []

    for index, action in enumerate(actions, start=1):
        legal_actions = get_legal_actions(state)
        if action not in legal_actions:
            raise ReplayConsistencyError(
                "Action is not legal on the accepted resolver path "
                f"at step {index}: {serialize_action(action)!r}",
            )

        draws = _predict_random_draws(state, action)
        next_state = apply_action(state, action)
        _assert_rng_alignment(state, next_state, draws, action, index)

        step = ReplayStep(
            index=index,
            before=summarize_state(state),
            action=action,
            events=_build_step_events(
                mission=mission,
                before_state=state,
                after_state=next_state,
                action=action,
                draws=draws,
                step_index=index,
            ),
            after=summarize_state(next_state),
        )
        steps.append(step)
        state = next_state

    trace = ReplayTrace(
        mission_id=mission.mission_id,
        initial_seed=seed,
        initial_rng_state=initial_rng_state,
        initial_state=initial_state,
        steps=tuple(steps),
        final_state=summarize_state(state),
    )
    return ReplayRunResult(final_state=state, trace=trace)


def replay_trace(mission: Mission, trace: ReplayTrace) -> ReplayRunResult:
    """Replay a previously recorded trace and verify it still matches the engine."""

    if mission.mission_id != trace.mission_id:
        raise ReplayConsistencyError(
            f"Trace mission_id {trace.mission_id!r} does not match mission {mission.mission_id!r}",
        )

    replayed = run_action_replay(mission, seed=trace.initial_seed, actions=trace.actions)

    if replayed.trace.initial_rng_state != trace.initial_rng_state:
        raise ReplayConsistencyError("Initial RNG state diverged before replay began")
    if replayed.trace.initial_state != trace.initial_state:
        raise ReplayConsistencyError("Initial state summary diverged before replay began")
    if replayed.trace != trace:
        raise ReplayConsistencyError("Recorded trace no longer matches resolver behavior")

    return replayed


def render_replay_trace(trace: ReplayTrace) -> str:
    """Render a deterministic human-readable log from structured replay data."""

    lines = [
        f"Mission {trace.mission_id} seed={trace.initial_seed} steps={len(trace.steps)}",
        (
            "Start "
            f"turn={trace.initial_state.turn} "
            f"phase={trace.initial_state.phase} "
            f"pending={trace.initial_state.pending_decision}"
        ),
    ]

    for step in trace.steps:
        lines.append(
            f"{step.index:02d} "
            f"T{step.before.turn} "
            f"{step.before.phase} "
            f"{_format_action(step.action)}"
        )
        for event in step.events:
            if event.kind is ReplayEventKind.ACTION_SELECTED:
                continue
            lines.append(f"   {_format_event(event)}")

    lines.append(
        "End "
        f"turn={trace.final_state.turn} "
        f"phase={trace.final_state.phase} "
        f"pending={trace.final_state.pending_decision} "
        f"terminal={trace.final_state.terminal_outcome}"
    )
    return "\n".join(lines)


def summarize_state(state: GameState) -> ReplayStateSummary:
    """Build a deterministic summary of a runtime state without mutating it."""

    return ReplayStateSummary(
        turn=state.turn,
        phase=state.phase.value,
        pending_decision=state.pending_decision.kind.value,
        terminal_outcome=None if state.terminal_outcome is None else state.terminal_outcome.value,
        activated_british_unit_ids=tuple(sorted(state.activated_british_unit_ids)),
        activated_german_unit_ids=tuple(sorted(state.activated_german_unit_ids)),
        current_activation=_summarize_activation(state.current_activation),
        british_units=tuple(
            ReplayBritishUnitSummary(
                unit_id=unit_id,
                unit_class=unit_state.unit_class,
                position=_coord_tuple(unit_state.position),
                morale=unit_state.morale.value,
                cover=unit_state.cover,
            )
            for unit_id, unit_state in sorted(state.british_units.items())
        ),
        german_units=tuple(
            ReplayGermanUnitSummary(
                unit_id=unit_id,
                unit_class=unit_state.unit_class,
                position=_coord_tuple(unit_state.position),
                facing=unit_state.facing.value,
                status=unit_state.status.value,
            )
            for unit_id, unit_state in sorted(state.german_units.items())
        ),
        unresolved_markers=tuple(
            ReplayMarkerSummary(
                marker_id=marker_id,
                position=_coord_tuple(marker_state.position),
            )
            for marker_id, marker_state in sorted(state.unresolved_markers.items())
        ),
    )


def serialize_action(action: GameAction) -> dict[str, Any]:
    """Return a JSON-friendly representation of a domain action."""

    if isinstance(action, SelectBritishUnitAction):
        return {"kind": action.kind.value, "unit_id": action.unit_id}
    if isinstance(action, ResolveDoubleChoiceAction):
        return {"kind": action.kind.value, "choice": action.choice.value}
    if isinstance(action, SelectActivationDieAction):
        return {"kind": action.kind.value, "die_value": action.die_value}
    if isinstance(action, DiscardActivationRollAction):
        return {"kind": action.kind.value}
    if isinstance(action, ChooseOrderExecutionAction):
        return {"kind": action.kind.value, "choice": action.choice.value}
    if isinstance(action, AdvanceAction):
        return {
            "kind": action.kind.value,
            "destination": _coord_dict(_coord_tuple(action.destination)),
        }
    if isinstance(action, FireAction):
        return {"kind": action.kind.value, "target_unit_id": action.target_unit_id}
    if isinstance(action, GrenadeAttackAction):
        return {"kind": action.kind.value, "target_unit_id": action.target_unit_id}
    if isinstance(action, TakeCoverAction):
        return {"kind": action.kind.value}
    if isinstance(action, RallyAction):
        return {"kind": action.kind.value}
    if isinstance(action, ScoutAction):
        payload: dict[str, Any] = {"kind": action.kind.value, "marker_id": action.marker_id}
        if action.facing is not None:
            payload["facing"] = action.facing.value
        return payload
    if isinstance(action, SelectGermanUnitAction):
        return {"kind": action.kind.value, "unit_id": action.unit_id}

    raise TypeError(f"Unsupported action type for replay serialization: {type(action)!r}")


def _summarize_activation(activation: CurrentActivation | None) -> ReplayActivationSummary | None:
    if activation is None:
        return None

    return ReplayActivationSummary(
        active_unit_id=activation.active_unit_id,
        roll=activation.roll,
        selected_die=activation.selected_die,
        planned_orders=tuple(order.value for order in activation.planned_orders),
        next_order_index=activation.next_order_index,
    )


def _predict_random_draws(state: GameState, action: GameAction) -> tuple[_PredictedRandomDraw, ...]:
    shadow_rng = DeterministicRNG.from_state(state.rng_state)
    draws: list[_PredictedRandomDraw] = []

    if isinstance(action, SelectBritishUnitAction):
        roll = shadow_rng.roll_nd6(2)
        draws.append(
            _PredictedRandomDraw(
                purpose="activation_roll",
                values=roll,
                details={"unit_id": action.unit_id},
            ),
        )
        return tuple(draws)

    if isinstance(action, ResolveDoubleChoiceAction):
        if action.choice is DoubleChoiceOption.REROLL:
            roll = shadow_rng.roll_nd6(2)
            active_unit_id = _require_active_unit_id(state)
            draws.append(
                _PredictedRandomDraw(
                    purpose="activation_reroll",
                    values=roll,
                    details={"unit_id": active_unit_id},
                ),
            )
        return tuple(draws)

    if isinstance(action, AdvanceAction):
        for marker_id in movement_reveal_marker_ids(state, action.destination):
            draws.append(
                _PredictedRandomDraw(
                    purpose="reveal_table",
                    values=(shadow_rng.roll_d6(),),
                    details={"marker_id": marker_id, "method": "movement"},
                ),
            )
        return tuple(draws)

    if isinstance(action, ScoutAction):
        draws.append(
            _PredictedRandomDraw(
                purpose="reveal_table",
                values=(shadow_rng.roll_d6(),),
                details={"marker_id": action.marker_id, "method": "scout"},
            ),
        )
        return tuple(draws)

    if isinstance(action, FireAction):
        draws.append(
            _PredictedRandomDraw(
                purpose="british_attack",
                values=shadow_rng.roll_nd6(2),
                details={
                    "attack_kind": action.kind.value,
                    "attacker_unit_id": _require_active_unit_id(state),
                    "target_unit_id": action.target_unit_id,
                },
            ),
        )
        return tuple(draws)

    if isinstance(action, GrenadeAttackAction):
        draws.append(
            _PredictedRandomDraw(
                purpose="british_attack",
                values=shadow_rng.roll_nd6(2),
                details={
                    "attack_kind": action.kind.value,
                    "attacker_unit_id": _require_active_unit_id(state),
                    "target_unit_id": action.target_unit_id,
                },
            ),
        )
        return tuple(draws)

    if isinstance(action, SelectGermanUnitAction):
        for target_unit_id in german_fire_target_ids(state, attacker_unit_id=action.unit_id):
            draws.append(
                _PredictedRandomDraw(
                    purpose="german_fire",
                    values=shadow_rng.roll_nd6(2),
                    details={
                        "attacker_unit_id": action.unit_id,
                        "target_unit_id": target_unit_id,
                    },
                ),
            )
        return tuple(draws)

    return ()


def _assert_rng_alignment(
    before_state: GameState,
    after_state: GameState,
    draws: tuple[_PredictedRandomDraw, ...],
    action: GameAction,
    step_index: int,
) -> None:
    shadow_rng = DeterministicRNG.from_state(before_state.rng_state)
    for draw in draws:
        if len(draw.values) == 1:
            consumed = (shadow_rng.roll_d6(),)
        else:
            consumed = shadow_rng.roll_nd6(len(draw.values))
        if consumed != draw.values:
            raise ReplayConsistencyError(
                "Predicted draw reconstruction diverged "
                f"at step {step_index}: {serialize_action(action)!r}",
            )

    expected_rng_state = shadow_rng.snapshot()
    if expected_rng_state != after_state.rng_state:
        raise ReplayConsistencyError(
            "Replay adapter no longer matches resolver RNG usage "
            f"at step {step_index}: {serialize_action(action)!r}",
        )


def _build_step_events(
    *,
    mission: Mission,
    before_state: GameState,
    after_state: GameState,
    action: GameAction,
    draws: tuple[_PredictedRandomDraw, ...],
    step_index: int,
) -> tuple[ReplayEvent, ...]:
    events: list[ReplayEvent] = [
        ReplayEvent(
            kind=ReplayEventKind.ACTION_SELECTED,
            details=serialize_action(action),
        ),
    ]
    events.extend(draw.to_event() for draw in draws)
    events.extend(_build_reveal_events(mission, before_state, after_state, action, draws))
    events.extend(
        _build_attack_events(
            mission,
            before_state,
            after_state,
            action,
            draws,
            step_index,
        ),
    )
    events.extend(_build_morale_change_events(before_state, after_state, action))
    events.extend(_build_unit_removed_events(before_state, after_state, action))

    if before_state.phase is not after_state.phase:
        events.append(
            ReplayEvent(
                kind=ReplayEventKind.PHASE_ADVANCED,
                details={
                    "from_phase": before_state.phase.value,
                    "to_phase": after_state.phase.value,
                },
            ),
        )

    if before_state.turn != after_state.turn:
        events.append(
            ReplayEvent(
                kind=ReplayEventKind.TURN_ADVANCED,
                details={
                    "from_turn": before_state.turn,
                    "to_turn": after_state.turn,
                },
            ),
        )

    if before_state.terminal_outcome is None and after_state.terminal_outcome is not None:
        events.append(
            ReplayEvent(
                kind=ReplayEventKind.TERMINAL_OUTCOME_SET,
                details={"outcome": after_state.terminal_outcome.value},
            ),
        )

    return tuple(events)


def _build_reveal_events(
    mission: Mission,
    before_state: GameState,
    after_state: GameState,
    action: GameAction,
    draws: tuple[_PredictedRandomDraw, ...],
) -> tuple[ReplayEvent, ...]:
    if not isinstance(action, (AdvanceAction, ScoutAction)):
        return ()

    method = "movement" if isinstance(action, AdvanceAction) else "scout"
    marker_ids = tuple(
        marker_id
        for marker_id in sorted(before_state.unresolved_markers)
        if marker_id not in after_state.unresolved_markers and marker_id in after_state.german_units
    )
    reveal_rolls = [draw for draw in draws if draw.purpose == "reveal_table"]

    if len(marker_ids) != len(reveal_rolls):
        raise ReplayConsistencyError("Reveal draw count does not match reveal state transition")

    events: list[ReplayEvent] = []
    for marker_id, draw in zip(marker_ids, reveal_rolls, strict=True):
        german_unit = after_state.german_units[marker_id]
        expected_unit_class = _reveal_table_result(mission, draw.values[0])
        if german_unit.unit_class != expected_unit_class:
            raise ReplayConsistencyError(
                f"Reveal-table reconstruction diverged for marker {marker_id!r}",
            )
        events.append(
            ReplayEvent(
                kind=ReplayEventKind.REVEAL_RESOLVED,
                details={
                    "marker_id": marker_id,
                    "method": method,
                    "roll": draw.values[0],
                    "unit_class": german_unit.unit_class,
                    "position": _coord_dict(_coord_tuple(german_unit.position)),
                    "facing": german_unit.facing.value,
                },
            ),
        )

    return tuple(events)


def _build_attack_events(
    mission: Mission,
    before_state: GameState,
    after_state: GameState,
    action: GameAction,
    draws: tuple[_PredictedRandomDraw, ...],
    step_index: int,
) -> tuple[ReplayEvent, ...]:
    if isinstance(action, FireAction):
        attacker = before_state.british_units[_require_active_unit_id(before_state)]
        defender = before_state.german_units[action.target_unit_id]
        threshold = calculate_fire_threshold(
            mission,
            attacker=attacker,
            defender=defender,
            british_units=before_state.british_units,
        )
        draw = _single_attack_draw(draws, step_index)
        hit = sum(draw.values) >= threshold
        actual_hit = (
            before_state.german_units[action.target_unit_id].status is GermanUnitStatus.ACTIVE
            and after_state.german_units[action.target_unit_id].status is GermanUnitStatus.REMOVED
        )
        if hit != actual_hit:
            raise ReplayConsistencyError("British fire replay reconstruction diverged")
        return (
            ReplayEvent(
                kind=ReplayEventKind.ATTACK_RESOLVED,
                details={
                    "side": "british",
                    "attack_kind": action.kind.value,
                    "attacker_unit_id": attacker.unit_id,
                    "target_unit_id": action.target_unit_id,
                    "threshold": threshold,
                    "roll": list(draw.values),
                    "roll_total": sum(draw.values),
                    "hit": hit,
                },
            ),
        )

    if isinstance(action, GrenadeAttackAction):
        attacker = before_state.british_units[_require_active_unit_id(before_state)]
        threshold = calculate_grenade_attack_threshold(
            mission,
            attacker=attacker,
        )
        draw = _single_attack_draw(draws, step_index)
        hit = sum(draw.values) >= threshold
        actual_hit = (
            before_state.german_units[action.target_unit_id].status is GermanUnitStatus.ACTIVE
            and after_state.german_units[action.target_unit_id].status is GermanUnitStatus.REMOVED
        )
        if hit != actual_hit:
            raise ReplayConsistencyError("Grenade replay reconstruction diverged")
        return (
            ReplayEvent(
                kind=ReplayEventKind.ATTACK_RESOLVED,
                details={
                    "side": "british",
                    "attack_kind": action.kind.value,
                    "attacker_unit_id": attacker.unit_id,
                    "target_unit_id": action.target_unit_id,
                    "threshold": threshold,
                    "roll": list(draw.values),
                    "roll_total": sum(draw.values),
                    "hit": hit,
                },
            ),
        )

    if isinstance(action, SelectGermanUnitAction):
        events: list[ReplayEvent] = []
        target_ids = german_fire_target_ids(before_state, attacker_unit_id=action.unit_id)
        if len(target_ids) != len(draws):
            raise ReplayConsistencyError("German fire draw count does not match target count")
        for target_unit_id, draw in zip(target_ids, draws, strict=True):
            threshold = calculate_german_fire_threshold(
                before_state,
                attacker_unit_id=action.unit_id,
                target_unit_id=target_unit_id,
            )
            hit = sum(draw.values) >= threshold
            actual_hit = (
                before_state.british_units[target_unit_id].morale
                != after_state.british_units[target_unit_id].morale
            )
            if hit != actual_hit:
                raise ReplayConsistencyError("German fire replay reconstruction diverged")
            events.append(
                ReplayEvent(
                    kind=ReplayEventKind.ATTACK_RESOLVED,
                    details={
                        "side": "german",
                        "attack_kind": "german_fire",
                        "attacker_unit_id": action.unit_id,
                        "target_unit_id": target_unit_id,
                        "threshold": threshold,
                        "roll": list(draw.values),
                        "roll_total": sum(draw.values),
                        "hit": hit,
                    },
                ),
            )
        return tuple(events)

    return ()


def _build_morale_change_events(
    before_state: GameState,
    after_state: GameState,
    action: GameAction,
) -> tuple[ReplayEvent, ...]:
    events: list[ReplayEvent] = []
    cause = _morale_cause(action)

    for unit_id in sorted(before_state.british_units):
        before_morale = before_state.british_units[unit_id].morale
        after_morale = after_state.british_units[unit_id].morale
        if before_morale is after_morale:
            continue
        events.append(
            ReplayEvent(
                kind=ReplayEventKind.MORALE_CHANGED,
                details={
                    "unit_id": unit_id,
                    "from_morale": before_morale.value,
                    "to_morale": after_morale.value,
                    "cause": cause,
                },
            ),
        )

    return tuple(events)


def _build_unit_removed_events(
    before_state: GameState,
    after_state: GameState,
    action: GameAction,
) -> tuple[ReplayEvent, ...]:
    events: list[ReplayEvent] = []
    cause = _removal_cause(action)

    for unit_id in sorted(before_state.german_units):
        if (
            before_state.german_units[unit_id].status is not GermanUnitStatus.REMOVED
            and after_state.german_units[unit_id].status is GermanUnitStatus.REMOVED
        ):
            events.append(
                ReplayEvent(
                    kind=ReplayEventKind.UNIT_REMOVED,
                    details={
                        "side": "german",
                        "unit_id": unit_id,
                        "cause": cause,
                    },
                ),
            )

    for unit_id in sorted(before_state.british_units):
        if (
            before_state.british_units[unit_id].morale is not BritishMorale.REMOVED
            and after_state.british_units[unit_id].morale is BritishMorale.REMOVED
        ):
            events.append(
                ReplayEvent(
                    kind=ReplayEventKind.UNIT_REMOVED,
                    details={
                        "side": "british",
                        "unit_id": unit_id,
                        "cause": cause,
                    },
                ),
            )

    return tuple(events)


def _single_attack_draw(
    draws: tuple[_PredictedRandomDraw, ...],
    step_index: int,
) -> _PredictedRandomDraw:
    if len(draws) != 1:
        raise ReplayConsistencyError(
            f"Expected exactly one attack draw at step {step_index}, got {len(draws)}",
        )
    return draws[0]


def _morale_cause(action: GameAction) -> str:
    if isinstance(action, RallyAction):
        return "rally"
    if isinstance(action, SelectGermanUnitAction):
        return "german_fire"
    return action.kind.value


def _removal_cause(action: GameAction) -> str:
    if isinstance(action, SelectGermanUnitAction):
        return "german_fire"
    return action.kind.value


def _reveal_table_result(mission: Mission, roll: int) -> str:
    for row in mission.german.reveal_table:
        if row.roll_min <= roll <= row.roll_max:
            return row.result_unit_class
    raise ReplayConsistencyError(f"Reveal-table roll {roll} was outside the mission table")


def _require_active_unit_id(state: GameState) -> str:
    if state.current_activation is None:
        raise ReplayConsistencyError("Replay expected an active British unit in current_activation")
    return state.current_activation.active_unit_id


def _format_action(action: GameAction) -> str:
    if isinstance(action, SelectBritishUnitAction):
        return f"select_british_unit(unit_id={action.unit_id})"
    if isinstance(action, ResolveDoubleChoiceAction):
        return f"resolve_double_choice(choice={action.choice.value})"
    if isinstance(action, SelectActivationDieAction):
        return f"select_activation_die(die_value={action.die_value})"
    if isinstance(action, DiscardActivationRollAction):
        return "discard_activation_roll()"
    if isinstance(action, ChooseOrderExecutionAction):
        return f"choose_order_execution(choice={action.choice.value})"
    if isinstance(action, AdvanceAction):
        return f"advance(destination={_format_coord_tuple(_coord_tuple(action.destination))})"
    if isinstance(action, FireAction):
        return f"fire(target_unit_id={action.target_unit_id})"
    if isinstance(action, GrenadeAttackAction):
        return f"grenade_attack(target_unit_id={action.target_unit_id})"
    if isinstance(action, TakeCoverAction):
        return "take_cover()"
    if isinstance(action, RallyAction):
        return "rally()"
    if isinstance(action, ScoutAction):
        return f"scout(marker_id={action.marker_id}, facing={action.facing.value})"
    if isinstance(action, SelectGermanUnitAction):
        return f"select_german_unit(unit_id={action.unit_id})"
    return action.kind.value


def _format_event(event: ReplayEvent) -> str:
    details = event.details
    if event.kind is ReplayEventKind.RANDOM_DRAW:
        return (
            f"random {details['purpose']} "
            f"{details['values']} "
            f"{_format_detail_suffix(details, skip={'purpose', 'values'})}"
        ).rstrip()

    if event.kind is ReplayEventKind.REVEAL_RESOLVED:
        return (
            f"reveal marker={details['marker_id']} "
            f"method={details['method']} "
            f"roll={details['roll']} "
            f"unit_class={details['unit_class']} "
            f"facing={details['facing']} "
            f"position={_format_coord_dict(details['position'])}"
        )

    if event.kind is ReplayEventKind.ATTACK_RESOLVED:
        return (
            f"attack {details['attack_kind']} "
            f"{details['attacker_unit_id']} -> {details['target_unit_id']} "
            f"roll={details['roll_total']} "
            f"threshold={details['threshold']} "
            f"hit={details['hit']}"
        )

    if event.kind is ReplayEventKind.MORALE_CHANGED:
        return (
            f"morale {details['unit_id']} "
            f"{details['from_morale']} -> {details['to_morale']} "
            f"cause={details['cause']}"
        )

    if event.kind is ReplayEventKind.UNIT_REMOVED:
        return (
            f"removed side={details['side']} "
            f"unit_id={details['unit_id']} "
            f"cause={details['cause']}"
        )

    if event.kind is ReplayEventKind.PHASE_ADVANCED:
        return f"phase {details['from_phase']} -> {details['to_phase']}"

    if event.kind is ReplayEventKind.TURN_ADVANCED:
        return f"turn {details['from_turn']} -> {details['to_turn']}"

    if event.kind is ReplayEventKind.TERMINAL_OUTCOME_SET:
        return f"terminal outcome={details['outcome']}"

    return f"{event.kind.value} {details}"


def _format_detail_suffix(details: dict[str, Any], *, skip: set[str]) -> str:
    parts = [
        f"{key}={value}"
        for key, value in details.items()
        if key not in skip
    ]
    return " ".join(parts)


def _coord_tuple(coord: HexCoord) -> tuple[int, int]:
    return (coord.q, coord.r)


def _coord_dict(coord: tuple[int, int]) -> dict[str, int]:
    return {"q": coord[0], "r": coord[1]}


def _format_coord_tuple(coord: tuple[int, int]) -> str:
    return f"({coord[0]}, {coord[1]})"


def _format_coord_dict(coord: dict[str, int]) -> str:
    return f"({coord['q']}, {coord['r']})"


def _serialize_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _serialize_value(inner_value) for key, inner_value in value.items()}
    if isinstance(value, tuple):
        return [_serialize_value(inner_value) for inner_value in value]
    if isinstance(value, list):
        return [_serialize_value(inner_value) for inner_value in value]
    return value


__all__ = [
    "ReplayConsistencyError",
    "ReplayEvent",
    "ReplayEventKind",
    "ReplayRunResult",
    "ReplayStateSummary",
    "ReplayStep",
    "ReplayTrace",
    "render_replay_trace",
    "replay_trace",
    "run_action_replay",
    "serialize_action",
    "summarize_state",
]
