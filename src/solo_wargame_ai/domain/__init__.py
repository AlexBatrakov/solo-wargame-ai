"""Core domain primitives for the Solo Wargame AI engine."""

from .enums import (
    CoordinateSystem,
    HexDirection,
    coordinate_system_from_name,
    hex_direction_from_name,
)
from .hexgrid import (
    ALL_DIRECTIONS,
    AXIAL_DIRECTION_DELTAS,
    BRITISH_FORWARD_DIRECTIONS,
    HexCoord,
    are_adjacent,
    british_forward_neighbors,
    neighbor,
    neighbors,
)
from .rng import DeterministicRNG, RNGState
from .terrain import TerrainType, is_terrain_name, terrain_from_name

__all__ = [
    "ALL_DIRECTIONS",
    "AXIAL_DIRECTION_DELTAS",
    "BRITISH_FORWARD_DIRECTIONS",
    "CoordinateSystem",
    "DeterministicRNG",
    "HexCoord",
    "HexDirection",
    "RNGState",
    "TerrainType",
    "are_adjacent",
    "british_forward_neighbors",
    "coordinate_system_from_name",
    "hex_direction_from_name",
    "is_terrain_name",
    "neighbor",
    "neighbors",
    "terrain_from_name",
]
