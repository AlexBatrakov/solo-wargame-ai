"""Small enums shared across early domain modules."""

from __future__ import annotations

from enum import StrEnum


class CoordinateSystem(StrEnum):
    """Supported board coordinate systems."""

    AXIAL_FLAT_TOP = "axial_flat_top"


class HexDirection(StrEnum):
    """Documented flat-top axial direction names."""

    UP_LEFT = "up_left"
    UP = "up"
    UP_RIGHT = "up_right"
    DOWN_RIGHT = "down_right"
    DOWN = "down"
    DOWN_LEFT = "down_left"


def coordinate_system_from_name(name: str) -> CoordinateSystem:
    """Parse a documented coordinate-system identifier."""

    try:
        return CoordinateSystem(name)
    except ValueError as exc:
        raise ValueError(f"Unknown coordinate system: {name}") from exc


def hex_direction_from_name(name: str) -> HexDirection:
    """Parse a documented hex-direction identifier."""

    try:
        return HexDirection(name)
    except ValueError as exc:
        raise ValueError(f"Unknown hex direction: {name}") from exc


__all__ = [
    "CoordinateSystem",
    "HexDirection",
    "coordinate_system_from_name",
    "hex_direction_from_name",
]
