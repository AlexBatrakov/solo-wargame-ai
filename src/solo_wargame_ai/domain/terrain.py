"""Minimal terrain primitives for board transcription and mission validation."""

from __future__ import annotations

from enum import StrEnum


class TerrainType(StrEnum):
    """Documented terrain identifiers used by board and mission data."""

    CLEAR = "clear"
    WOODS = "woods"
    BUILDING = "building"
    HILL = "hill"
    RIVER = "river"


def terrain_from_name(name: str) -> TerrainType:
    """Parse a terrain identifier from mission/config data."""

    try:
        return TerrainType(name)
    except ValueError as exc:
        raise ValueError(f"Unknown terrain type: {name}") from exc


def is_terrain_name(name: str) -> bool:
    """Return whether the name is a supported terrain identifier."""

    try:
        terrain_from_name(name)
    except ValueError:
        return False
    return True


__all__ = ["TerrainType", "is_terrain_name", "terrain_from_name"]
