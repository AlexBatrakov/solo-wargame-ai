"""Hex-grid helpers for the documented flat-top axial map convention."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Iterable

from .enums import HexDirection


@dataclass(frozen=True, slots=True, order=True)
class HexCoord:
    """An axial flat-top hex coordinate."""

    q: int
    r: int


ALL_DIRECTIONS: tuple[HexDirection, ...] = tuple(HexDirection)

BRITISH_FORWARD_DIRECTIONS: tuple[HexDirection, ...] = (
    HexDirection.UP_LEFT,
    HexDirection.UP,
    HexDirection.UP_RIGHT,
)

AXIAL_DIRECTION_DELTAS = MappingProxyType(
    {
        HexDirection.UP_LEFT: HexCoord(-1, 0),
        HexDirection.UP: HexCoord(0, -1),
        HexDirection.UP_RIGHT: HexCoord(1, -1),
        HexDirection.DOWN_RIGHT: HexCoord(1, 0),
        HexDirection.DOWN: HexCoord(0, 1),
        HexDirection.DOWN_LEFT: HexCoord(-1, 1),
    }
)


def neighbor(coord: HexCoord, direction: HexDirection) -> HexCoord:
    """Return the adjacent hex in the requested direction."""

    delta = AXIAL_DIRECTION_DELTAS[direction]
    return HexCoord(q=coord.q + delta.q, r=coord.r + delta.r)


def neighbors(
    coord: HexCoord,
    directions: Iterable[HexDirection] = ALL_DIRECTIONS,
) -> tuple[HexCoord, ...]:
    """Return adjacent hexes in the same order as the requested directions."""

    return tuple(neighbor(coord, direction) for direction in directions)


def are_adjacent(first: HexCoord, second: HexCoord) -> bool:
    """Return True when two hexes share an edge."""

    delta_q = second.q - first.q
    delta_r = second.r - first.r
    return any(
        delta_q == direction_delta.q and delta_r == direction_delta.r
        for direction_delta in AXIAL_DIRECTION_DELTAS.values()
    )


def british_forward_neighbors(
    coord: HexCoord,
    forward_directions: Iterable[HexDirection] = BRITISH_FORWARD_DIRECTIONS,
) -> tuple[HexCoord, ...]:
    """Return the forward-adjacent hexes for the supplied map orientation."""

    return neighbors(coord, directions=tuple(forward_directions))


__all__ = [
    "ALL_DIRECTIONS",
    "AXIAL_DIRECTION_DELTAS",
    "BRITISH_FORWARD_DIRECTIONS",
    "HexCoord",
    "are_adjacent",
    "british_forward_neighbors",
    "neighbor",
    "neighbors",
]
