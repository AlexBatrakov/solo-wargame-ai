"""Stage 3B action contract objects without legality or resolution logic."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import ClassVar, TypeAlias

from .enums import HexDirection
from .hexgrid import HexCoord


class ActionKind(StrEnum):
    """Tagged action kinds used by the staged Mission 1 action contract."""

    SELECT_BRITISH_UNIT = "select_british_unit"
    RESOLVE_DOUBLE_CHOICE = "resolve_double_choice"
    SELECT_ACTIVATION_DIE = "select_activation_die"
    DISCARD_ACTIVATION_ROLL = "discard_activation_roll"
    CHOOSE_ORDER_EXECUTION = "choose_order_execution"
    ADVANCE = "advance"
    FIRE = "fire"
    GRENADE_ATTACK = "grenade_attack"
    TAKE_COVER = "take_cover"
    RALLY = "rally"
    SCOUT = "scout"
    SELECT_GERMAN_UNIT = "select_german_unit"


class DoubleChoiceOption(StrEnum):
    """Ways to resolve a rolled double during British activation."""

    KEEP = "keep"
    REROLL = "reroll"


class OrderExecutionChoice(StrEnum):
    """How to execute the selected Orders Chart row."""

    FIRST_ORDER_ONLY = "first_order_only"
    SECOND_ORDER_ONLY = "second_order_only"
    BOTH_ORDERS = "both_orders"
    NO_ACTION = "no_action"


@dataclass(frozen=True, slots=True)
class SelectBritishUnitAction:
    """Select the next British unit to activate."""

    unit_id: str
    kind: ClassVar[ActionKind] = ActionKind.SELECT_BRITISH_UNIT


@dataclass(frozen=True, slots=True)
class ResolveDoubleChoiceAction:
    """Resolve whether a rolled double is kept or rerolled."""

    choice: DoubleChoiceOption
    kind: ClassVar[ActionKind] = ActionKind.RESOLVE_DOUBLE_CHOICE


@dataclass(frozen=True, slots=True)
class SelectActivationDieAction:
    """Select one die result from the current accepted roll."""

    die_value: int
    kind: ClassVar[ActionKind] = ActionKind.SELECT_ACTIVATION_DIE


@dataclass(frozen=True, slots=True)
class DiscardActivationRollAction:
    """Discard the current activation roll and perform no orders."""

    kind: ClassVar[ActionKind] = ActionKind.DISCARD_ACTIVATION_ROLL


@dataclass(frozen=True, slots=True)
class ChooseOrderExecutionAction:
    """Choose whether to execute the first order, second order, both, or none."""

    choice: OrderExecutionChoice
    kind: ClassVar[ActionKind] = ActionKind.CHOOSE_ORDER_EXECUTION


@dataclass(frozen=True, slots=True)
class AdvanceAction:
    """Choose the destination hex for an advance order."""

    destination: HexCoord
    kind: ClassVar[ActionKind] = ActionKind.ADVANCE


@dataclass(frozen=True, slots=True)
class FireAction:
    """Choose the adjacent revealed German unit to fire at."""

    target_unit_id: str
    kind: ClassVar[ActionKind] = ActionKind.FIRE


@dataclass(frozen=True, slots=True)
class GrenadeAttackAction:
    """Choose the adjacent revealed German unit to attack with grenades."""

    target_unit_id: str
    kind: ClassVar[ActionKind] = ActionKind.GRENADE_ATTACK


@dataclass(frozen=True, slots=True)
class TakeCoverAction:
    """Choose to spend the order taking cover."""

    kind: ClassVar[ActionKind] = ActionKind.TAKE_COVER


@dataclass(frozen=True, slots=True)
class RallyAction:
    """Choose to spend the order rallying the active British unit."""

    kind: ClassVar[ActionKind] = ActionKind.RALLY


@dataclass(frozen=True, slots=True)
class ScoutAction:
    """Choose the hidden marker to scout and an optional scout-facing parameter."""

    marker_id: str
    facing: HexDirection | None = None
    kind: ClassVar[ActionKind] = ActionKind.SCOUT


@dataclass(frozen=True, slots=True)
class SelectGermanUnitAction:
    """Select the next revealed German unit to activate."""

    unit_id: str
    kind: ClassVar[ActionKind] = ActionKind.SELECT_GERMAN_UNIT


GameAction: TypeAlias = (
    SelectBritishUnitAction
    | ResolveDoubleChoiceAction
    | SelectActivationDieAction
    | DiscardActivationRollAction
    | ChooseOrderExecutionAction
    | AdvanceAction
    | FireAction
    | GrenadeAttackAction
    | TakeCoverAction
    | RallyAction
    | ScoutAction
    | SelectGermanUnitAction
)


__all__ = [
    "ActionKind",
    "AdvanceAction",
    "ChooseOrderExecutionAction",
    "DiscardActivationRollAction",
    "DoubleChoiceOption",
    "FireAction",
    "GameAction",
    "GrenadeAttackAction",
    "OrderExecutionChoice",
    "RallyAction",
    "ResolveDoubleChoiceAction",
    "ScoutAction",
    "SelectActivationDieAction",
    "SelectBritishUnitAction",
    "SelectGermanUnitAction",
    "TakeCoverAction",
]
