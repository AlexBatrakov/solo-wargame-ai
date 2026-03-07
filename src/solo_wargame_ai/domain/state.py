"""Runtime state contract and validation for Stage 3B."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType
from typing import Iterable, Mapping

from .decision_context import (
    ChooseBritishUnitContext,
    ChooseOrderParameterContext,
    DecisionContextKind,
    PendingDecision,
    context_requires_current_activation,
)
from .enums import HexDirection
from .mission import Mission, OrderName
from .rng import DeterministicRNG, RNGState
from .units import (
    BritishMorale,
    BritishUnitState,
    GermanUnitStatus,
    RevealedGermanUnitState,
    UnresolvedHiddenMarkerState,
)

DEFAULT_INITIAL_RNG_SEED = 0


class GamePhase(StrEnum):
    """Top-level turn phases supported by the Stage 3B runtime model."""

    BRITISH = "british"
    GERMAN = "german"


@dataclass(frozen=True, slots=True)
class CurrentActivation:
    """In-progress British activation bookkeeping."""

    active_unit_id: str
    roll: tuple[int, int] | None = None
    selected_die: int | None = None
    planned_orders: tuple[OrderName, ...] = ()
    next_order_index: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(self, "planned_orders", tuple(self.planned_orders))

    @property
    def active_order(self) -> OrderName | None:
        """Return the next staged order to parameterize, if one exists."""

        if 0 <= self.next_order_index < len(self.planned_orders):
            return self.planned_orders[self.next_order_index]
        return None


@dataclass(frozen=True, slots=True)
class GameStateValidationIssue:
    """One runtime validation issue with a location and human-readable message."""

    path: str
    message: str

    def __str__(self) -> str:
        return f"{self.path}: {self.message}"


class GameStateValidationError(ValueError):
    """Raised when runtime state violates the Stage 3B contract."""

    def __init__(self, issues: Iterable[GameStateValidationIssue]) -> None:
        issue_tuple = tuple(issues)
        if not issue_tuple:
            raise ValueError("GameStateValidationError requires at least one issue")

        self.issues = issue_tuple
        super().__init__("; ".join(str(issue) for issue in issue_tuple))


class _GameStateValidationCollector:
    """Collect runtime validation issues before raising a single error."""

    def __init__(self) -> None:
        self._issues: list[GameStateValidationIssue] = []

    def add(self, path: str, message: str) -> None:
        self._issues.append(GameStateValidationIssue(path=path, message=message))

    def raise_if_any(self) -> None:
        if self._issues:
            raise GameStateValidationError(self._issues)


@dataclass(frozen=True, slots=True)
class GameState:
    """Dynamic runtime truth for one mission instance."""

    mission: Mission
    turn: int
    phase: GamePhase
    british_units: Mapping[str, BritishUnitState]
    german_units: Mapping[str, RevealedGermanUnitState] = field(default_factory=dict)
    unresolved_markers: Mapping[str, UnresolvedHiddenMarkerState] = field(default_factory=dict)
    activated_british_unit_ids: frozenset[str] = field(default_factory=frozenset)
    activated_german_unit_ids: frozenset[str] = field(default_factory=frozenset)
    pending_decision: PendingDecision = field(default_factory=ChooseBritishUnitContext)
    current_activation: CurrentActivation | None = None
    rng_state: RNGState = field(
        default_factory=lambda: DeterministicRNG(seed=DEFAULT_INITIAL_RNG_SEED).snapshot(),
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "british_units", MappingProxyType(dict(self.british_units)))
        object.__setattr__(self, "german_units", MappingProxyType(dict(self.german_units)))
        object.__setattr__(
            self,
            "unresolved_markers",
            MappingProxyType(dict(self.unresolved_markers)),
        )
        object.__setattr__(
            self,
            "activated_british_unit_ids",
            frozenset(self.activated_british_unit_ids),
        )
        object.__setattr__(
            self,
            "activated_german_unit_ids",
            frozenset(self.activated_german_unit_ids),
        )


def create_initial_game_state(
    mission: Mission,
    *,
    seed: int | None = DEFAULT_INITIAL_RNG_SEED,
) -> GameState:
    """Build the deterministic initial Mission 1 runtime state from a loaded mission."""

    if len(mission.map.start_hexes) != 1:
        raise ValueError("Stage 3B initial state construction expects exactly one start hex")

    start_hex = mission.map.start_hexes[0]
    state = GameState(
        mission=mission,
        turn=1,
        phase=GamePhase.BRITISH,
        british_units={
            unit.unit_id: BritishUnitState(
                unit_id=unit.unit_id,
                unit_class=unit.unit_class,
                position=start_hex,
                morale=BritishMorale.NORMAL,
                cover=0,
            )
            for unit in mission.british.roster
        },
        german_units={},
        unresolved_markers={
            marker.marker_id: UnresolvedHiddenMarkerState(
                marker_id=marker.marker_id,
                position=marker.coord,
            )
            for marker in mission.map.hidden_markers
        },
        activated_british_unit_ids=frozenset(),
        activated_german_unit_ids=frozenset(),
        pending_decision=ChooseBritishUnitContext(),
        current_activation=None,
        rng_state=DeterministicRNG(seed=seed).snapshot(),
    )
    validate_game_state(state)
    return state


def validate_game_state(state: GameState) -> None:
    """Validate Stage 3B runtime invariants for a game state snapshot."""

    collector = _GameStateValidationCollector()

    _validate_core_fields(state, collector)
    _validate_british_units(state, collector)
    _validate_german_units(state, collector)
    _validate_unresolved_markers(state, collector)
    _validate_occupancy(state, collector)
    _validate_activation_bookkeeping(state, collector)
    _validate_pending_decision(state, collector)

    collector.raise_if_any()


def _validate_core_fields(
    state: GameState,
    collector: _GameStateValidationCollector,
) -> None:
    if state.turn < 1:
        collector.add("turn", "turn must be at least 1")

    if not isinstance(state.phase, GamePhase):
        collector.add("phase", "phase must be a GamePhase value")


def _validate_british_units(
    state: GameState,
    collector: _GameStateValidationCollector,
) -> None:
    mission_roster = {unit.unit_id: unit for unit in state.mission.british.roster}

    for unit_id, mission_unit in mission_roster.items():
        if unit_id not in state.british_units:
            collector.add(
                "british_units",
                f"missing runtime unit for mission roster id {unit_id!r}",
            )
            continue

        unit_state = state.british_units[unit_id]
        if unit_state.unit_id != unit_id:
            collector.add(
                f"british_units.{unit_id}.unit_id",
                "mapping key must match runtime unit_id",
            )
        if unit_state.unit_class != mission_unit.unit_class:
            collector.add(
                f"british_units.{unit_id}.unit_class",
                "runtime unit_class must match the attached Mission roster",
            )
        if not isinstance(unit_state.morale, BritishMorale):
            collector.add(
                f"british_units.{unit_id}.morale",
                "morale must be a BritishMorale value",
            )
        if unit_state.cover < 0:
            collector.add(
                f"british_units.{unit_id}.cover",
                "cover must be non-negative",
            )
        if not state.mission.map.is_playable_hex(unit_state.position):
            collector.add(
                f"british_units.{unit_id}.position",
                "runtime unit position must be on a playable hex",
            )

    extra_unit_ids = sorted(set(state.british_units) - set(mission_roster))
    for unit_id in extra_unit_ids:
        collector.add(
            f"british_units.{unit_id}",
            "runtime British unit id does not exist in the attached Mission roster",
        )


def _validate_german_units(
    state: GameState,
    collector: _GameStateValidationCollector,
) -> None:
    mission_hidden_marker_ids = set(state.mission.map.hidden_markers_by_id)
    mission_german_classes = state.mission.german.unit_classes_by_name

    for unit_id, unit_state in state.german_units.items():
        if unit_state.unit_id != unit_id:
            collector.add(
                f"german_units.{unit_id}.unit_id",
                "mapping key must match runtime unit_id",
            )
        if unit_state.unit_id not in mission_hidden_marker_ids:
            collector.add(
                f"german_units.{unit_id}.unit_id",
                "runtime German unit id must correspond to a mission hidden marker id",
            )
        else:
            mission_marker = state.mission.map.hidden_markers_by_id[unit_state.unit_id]
            if unit_state.position != mission_marker.coord:
                collector.add(
                    f"german_units.{unit_id}.position",
                    "runtime German unit position must match its mission marker hex",
                )
        if unit_state.unit_class not in mission_german_classes:
            collector.add(
                f"german_units.{unit_id}.unit_class",
                "runtime German unit_class must exist in the attached Mission",
            )
        if not state.mission.map.is_playable_hex(unit_state.position):
            collector.add(
                f"german_units.{unit_id}.position",
                "runtime unit position must be on a playable hex",
            )
        if not isinstance(unit_state.facing, HexDirection):
            collector.add(
                f"german_units.{unit_id}.facing",
                "facing must be a HexDirection value",
            )
        if not isinstance(unit_state.status, GermanUnitStatus):
            collector.add(
                f"german_units.{unit_id}.status",
                "status must be a GermanUnitStatus value",
            )


def _validate_unresolved_markers(
    state: GameState,
    collector: _GameStateValidationCollector,
) -> None:
    mission_markers = state.mission.map.hidden_markers_by_id

    for marker_id, marker_state in state.unresolved_markers.items():
        if marker_state.marker_id != marker_id:
            collector.add(
                f"unresolved_markers.{marker_id}.marker_id",
                "mapping key must match runtime marker_id",
            )
        mission_marker = mission_markers.get(marker_id)
        if mission_marker is None:
            collector.add(
                f"unresolved_markers.{marker_id}",
                "runtime marker id does not exist in the attached Mission",
            )
            continue
        if marker_state.position != mission_marker.coord:
            collector.add(
                f"unresolved_markers.{marker_id}.position",
                "runtime unresolved marker position must match the attached Mission",
            )
        if not state.mission.map.is_playable_hex(marker_state.position):
            collector.add(
                f"unresolved_markers.{marker_id}.position",
                "runtime marker position must be on a playable hex",
            )


def _validate_occupancy(
    state: GameState,
    collector: _GameStateValidationCollector,
) -> None:
    british_by_position: dict[object, list[str]] = {}
    for unit_id, unit_state in state.british_units.items():
        british_by_position.setdefault(unit_state.position, []).append(unit_id)

    german_by_position: dict[object, list[str]] = {}
    for unit_id, unit_state in state.german_units.items():
        if unit_state.status is GermanUnitStatus.REMOVED:
            continue
        german_by_position.setdefault(unit_state.position, []).append(unit_id)

    for position, british_unit_ids in british_by_position.items():
        german_unit_ids = german_by_position.get(position)
        if german_unit_ids:
            collector.add(
                "occupancy",
                "British and German units may not occupy the same hex: "
                f"{position!r} has British {british_unit_ids!r} and German {german_unit_ids!r}",
            )

    for marker_id, marker_state in state.unresolved_markers.items():
        overlapping_germans = german_by_position.get(marker_state.position)
        if overlapping_germans:
            collector.add(
                f"unresolved_markers.{marker_id}.position",
                "an unresolved marker may not overlap a revealed German unit",
            )


def _validate_activation_bookkeeping(
    state: GameState,
    collector: _GameStateValidationCollector,
) -> None:
    for unit_id in sorted(state.activated_british_unit_ids):
        if unit_id not in state.british_units:
            collector.add(
                "activated_british_unit_ids",
                f"activated British unit id {unit_id!r} does not exist in runtime state",
            )

    for unit_id in sorted(state.activated_german_unit_ids):
        if unit_id not in state.german_units:
            collector.add(
                "activated_german_unit_ids",
                f"activated German unit id {unit_id!r} does not exist in runtime state",
            )

    if state.current_activation is None:
        return

    active_unit = state.british_units.get(state.current_activation.active_unit_id)
    if active_unit is None:
        collector.add(
            "current_activation.active_unit_id",
            "active_unit_id must reference an existing British runtime unit",
        )
        return

    if active_unit.morale is BritishMorale.REMOVED:
        collector.add(
            "current_activation.active_unit_id",
            "active_unit_id may not reference a removed British unit",
        )

    if state.current_activation.active_unit_id in state.activated_british_unit_ids:
        collector.add(
            "current_activation.active_unit_id",
            "the currently activating British unit must not already be marked activated",
        )


def _validate_pending_decision(
    state: GameState,
    collector: _GameStateValidationCollector,
) -> None:
    pending_kind = getattr(state.pending_decision, "kind", None)
    if not isinstance(pending_kind, DecisionContextKind):
        collector.add(
            "pending_decision",
            "pending_decision must be one of the declared decision-context objects",
        )
        return

    if state.phase is GamePhase.BRITISH and pending_kind is DecisionContextKind.CHOOSE_GERMAN_UNIT:
        collector.add(
            "pending_decision",
            "German-unit choice is only valid during the German phase",
        )

    if (
        state.phase is GamePhase.GERMAN
        and pending_kind is not DecisionContextKind.CHOOSE_GERMAN_UNIT
    ):
        collector.add(
            "pending_decision",
            "the German phase must expose CHOOSE_GERMAN_UNIT as its pending decision",
        )

    requires_activation = context_requires_current_activation(pending_kind)
    if requires_activation and state.current_activation is None:
        collector.add(
            "current_activation",
            "current_activation is required for the pending decision",
        )
        return

    if not requires_activation and state.current_activation is not None:
        collector.add(
            "current_activation",
            "current_activation must be empty for the pending decision",
        )
        return

    if state.current_activation is None:
        return

    activation = state.current_activation

    if activation.roll is not None:
        if len(activation.roll) != 2:
            collector.add("current_activation.roll", "roll must contain exactly two dice")
        for die_index, die_value in enumerate(activation.roll):
            if die_value < 1 or die_value > 6:
                collector.add(
                    f"current_activation.roll[{die_index}]",
                    "roll values must be between 1 and 6",
                )

    if activation.selected_die is not None:
        if activation.roll is None:
            collector.add(
                "current_activation.selected_die",
                "selected_die requires an accepted activation roll",
            )
        elif activation.selected_die not in activation.roll:
            collector.add(
                "current_activation.selected_die",
                "selected_die must come from the accepted activation roll",
            )

    if activation.next_order_index < 0:
        collector.add(
            "current_activation.next_order_index",
            "next_order_index must be non-negative",
        )

    if not activation.planned_orders and activation.next_order_index != 0:
        collector.add(
            "current_activation.next_order_index",
            "next_order_index must be 0 when no orders are planned",
        )

    if activation.next_order_index > len(activation.planned_orders):
        collector.add(
            "current_activation.next_order_index",
            "next_order_index may not exceed the number of planned orders",
        )

    for order_index, order in enumerate(activation.planned_orders):
        if not isinstance(order, OrderName):
            collector.add(
                f"current_activation.planned_orders[{order_index}]",
                "planned orders must be OrderName values",
            )

    if pending_kind is DecisionContextKind.CHOOSE_DOUBLE_CHOICE:
        if activation.roll is None:
            collector.add("current_activation.roll", "double-choice context requires a roll")
        elif activation.roll[0] != activation.roll[1]:
            collector.add(
                "current_activation.roll",
                "double-choice context requires a rolled double",
            )
        if activation.selected_die is not None:
            collector.add(
                "current_activation.selected_die",
                "selected_die must be empty before the double choice is resolved",
            )
        if activation.planned_orders:
            collector.add(
                "current_activation.planned_orders",
                "planned_orders must be empty during the double-choice context",
            )
        if activation.next_order_index != 0:
            collector.add(
                "current_activation.next_order_index",
                "next_order_index must be 0 during the double-choice context",
            )

    elif pending_kind is DecisionContextKind.CHOOSE_ACTIVATION_DIE:
        if activation.roll is None:
            collector.add("current_activation.roll", "die-choice context requires a roll")
        if activation.selected_die is not None:
            collector.add(
                "current_activation.selected_die",
                "selected_die must be empty while choosing the activation die",
            )
        if activation.planned_orders:
            collector.add(
                "current_activation.planned_orders",
                "planned_orders must be empty while choosing the activation die",
            )
        if activation.next_order_index != 0:
            collector.add(
                "current_activation.next_order_index",
                "next_order_index must be 0 while choosing the activation die",
            )

    elif pending_kind is DecisionContextKind.CHOOSE_ORDER_EXECUTION:
        if activation.roll is None:
            collector.add(
                "current_activation.roll",
                "order-execution context requires an accepted activation roll",
            )
        if activation.selected_die is None:
            collector.add(
                "current_activation.selected_die",
                "order-execution context requires a selected die",
            )
        if activation.planned_orders:
            collector.add(
                "current_activation.planned_orders",
                "planned_orders must still be empty before order execution is chosen",
            )
        if activation.next_order_index != 0:
            collector.add(
                "current_activation.next_order_index",
                "next_order_index must be 0 before order execution is chosen",
            )

    elif pending_kind is DecisionContextKind.CHOOSE_ORDER_PARAMETER:
        context = state.pending_decision
        if not isinstance(context, ChooseOrderParameterContext):
            collector.add(
                "pending_decision",
                "CHOOSE_ORDER_PARAMETER must use ChooseOrderParameterContext",
            )
            return

        if activation.roll is None:
            collector.add(
                "current_activation.roll",
                "order-parameter context requires an accepted activation roll",
            )
        if activation.selected_die is None:
            collector.add(
                "current_activation.selected_die",
                "order-parameter context requires a selected die",
            )
        if not activation.planned_orders:
            collector.add(
                "current_activation.planned_orders",
                "order-parameter context requires staged planned orders",
            )
        if context.order_index != activation.next_order_index:
            collector.add(
                "pending_decision.order_index",
                "order_index must match current_activation.next_order_index",
            )
        if not 0 <= context.order_index < len(activation.planned_orders):
            collector.add(
                "pending_decision.order_index",
                "order_index must point at a planned order",
            )
        elif activation.planned_orders[context.order_index] is not context.order:
            collector.add(
                "pending_decision.order",
                "pending order parameter must match the staged planned order",
            )


__all__ = [
    "CurrentActivation",
    "DEFAULT_INITIAL_RNG_SEED",
    "GamePhase",
    "GameState",
    "GameStateValidationError",
    "GameStateValidationIssue",
    "create_initial_game_state",
    "validate_game_state",
]
