"""Runtime unit and marker state for the staged Mission 1 engine."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .enums import HexDirection
from .hexgrid import HexCoord


class BritishMorale(StrEnum):
    """British morale ladder supported by the Mission 1 runtime model."""

    NORMAL = "normal"
    LOW = "low"
    REMOVED = "removed"


class GermanUnitStatus(StrEnum):
    """Runtime lifecycle state for a revealed German unit."""

    ACTIVE = "active"
    REMOVED = "removed"


@dataclass(frozen=True, slots=True)
class BritishUnitState:
    """Dynamic runtime state for one British unit."""

    unit_id: str
    unit_class: str
    position: HexCoord
    morale: BritishMorale
    cover: int


@dataclass(frozen=True, slots=True)
class RevealedGermanUnitState:
    """Dynamic runtime state for one revealed German unit."""

    unit_id: str
    unit_class: str
    position: HexCoord
    facing: HexDirection
    status: GermanUnitStatus


@dataclass(frozen=True, slots=True)
class UnresolvedHiddenMarkerState:
    """Dynamic runtime state for one unresolved hidden marker."""

    marker_id: str
    position: HexCoord


__all__ = [
    "BritishMorale",
    "BritishUnitState",
    "GermanUnitStatus",
    "RevealedGermanUnitState",
    "UnresolvedHiddenMarkerState",
]
