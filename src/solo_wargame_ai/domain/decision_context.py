"""Pending-decision contract for the staged Mission 1 runtime flow."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import ClassVar, TypeAlias

from .mission import OrderName


class DecisionContextKind(StrEnum):
    """Decision-context kinds that Stage 3B must make explicit in state."""

    CHOOSE_BRITISH_UNIT = "choose_british_unit"
    CHOOSE_DOUBLE_CHOICE = "choose_double_choice"
    CHOOSE_ACTIVATION_DIE = "choose_activation_die"
    CHOOSE_ORDER_EXECUTION = "choose_order_execution"
    CHOOSE_ORDER_PARAMETER = "choose_order_parameter"
    CHOOSE_GERMAN_UNIT = "choose_german_unit"


_CONTEXTS_REQUIRING_CURRENT_ACTIVATION = frozenset(
    {
        DecisionContextKind.CHOOSE_DOUBLE_CHOICE,
        DecisionContextKind.CHOOSE_ACTIVATION_DIE,
        DecisionContextKind.CHOOSE_ORDER_EXECUTION,
        DecisionContextKind.CHOOSE_ORDER_PARAMETER,
    },
)


def context_requires_current_activation(kind: DecisionContextKind) -> bool:
    """Return whether the pending-decision kind requires British activation state."""

    return kind in _CONTEXTS_REQUIRING_CURRENT_ACTIVATION


@dataclass(frozen=True, slots=True)
class ChooseBritishUnitContext:
    """Pending choice of the next British unit to activate."""

    kind: ClassVar[DecisionContextKind] = DecisionContextKind.CHOOSE_BRITISH_UNIT


@dataclass(frozen=True, slots=True)
class ChooseDoubleChoiceContext:
    """Pending choice to keep or reroll a rolled double."""

    kind: ClassVar[DecisionContextKind] = DecisionContextKind.CHOOSE_DOUBLE_CHOICE


@dataclass(frozen=True, slots=True)
class ChooseActivationDieContext:
    """Pending choice of which die result from the accepted roll to keep."""

    kind: ClassVar[DecisionContextKind] = DecisionContextKind.CHOOSE_ACTIVATION_DIE


@dataclass(frozen=True, slots=True)
class ChooseOrderExecutionContext:
    """Pending choice of how to execute the selected Orders Chart row."""

    kind: ClassVar[DecisionContextKind] = DecisionContextKind.CHOOSE_ORDER_EXECUTION


@dataclass(frozen=True, slots=True)
class ChooseOrderParameterContext:
    """Pending choice of concrete parameters for the next staged order."""

    order: OrderName
    order_index: int
    kind: ClassVar[DecisionContextKind] = DecisionContextKind.CHOOSE_ORDER_PARAMETER


@dataclass(frozen=True, slots=True)
class ChooseGermanUnitContext:
    """Pending choice of the next revealed German unit to activate."""

    kind: ClassVar[DecisionContextKind] = DecisionContextKind.CHOOSE_GERMAN_UNIT


PendingDecision: TypeAlias = (
    ChooseBritishUnitContext
    | ChooseDoubleChoiceContext
    | ChooseActivationDieContext
    | ChooseOrderExecutionContext
    | ChooseOrderParameterContext
    | ChooseGermanUnitContext
)


__all__ = [
    "ChooseActivationDieContext",
    "ChooseBritishUnitContext",
    "ChooseDoubleChoiceContext",
    "ChooseGermanUnitContext",
    "ChooseOrderExecutionContext",
    "ChooseOrderParameterContext",
    "DecisionContextKind",
    "PendingDecision",
    "context_requires_current_activation",
]
