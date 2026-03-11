"""Reveal helpers for the current hidden-marker mechanics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .enums import HexDirection
from .hexgrid import HexCoord, are_adjacent, neighbor
from .mission import Mission
from .rng import DeterministicRNG
from .state import GameState
from .units import GermanUnitStatus, RevealedGermanUnitState, UnresolvedHiddenMarkerState

DOWNWARD_FACING_DIRECTIONS: tuple[HexDirection, ...] = (
    HexDirection.DOWN_LEFT,
    HexDirection.DOWN,
    HexDirection.DOWN_RIGHT,
)


@dataclass(frozen=True, slots=True)
class RevealResolution:
    """Updated runtime enemy state after resolving one reveal mechanic."""

    german_units: Mapping[str, RevealedGermanUnitState]
    unresolved_markers: Mapping[str, UnresolvedHiddenMarkerState]
    revealed_marker_ids: tuple[str, ...]


def sample_reveal_unit_class(mission: Mission, rng: DeterministicRNG) -> str:
    """Sample one German unit class from the mission reveal table."""

    roll = rng.roll_d6()
    for row in mission.german.reveal_table:
        if row.roll_min <= roll <= row.roll_max:
            return row.result_unit_class
    raise AssertionError(f"Reveal-table roll {roll} was not covered by the mission table")


def movement_reveal_marker_ids(state: GameState, destination: HexCoord) -> tuple[str, ...]:
    """Return unresolved marker ids revealed by moving into ``destination``."""

    return tuple(
        marker.marker_id
        for marker in state.mission.map.hidden_markers
        if marker.marker_id in state.unresolved_markers
        and are_adjacent(destination, state.unresolved_markers[marker.marker_id].position)
    )


def legal_scout_facing_directions(
    mission: Mission,
    marker_position: HexCoord,
) -> tuple[HexDirection, ...]:
    """Return legal downward-facing scout choices for a revealed marker hex."""

    return tuple(
        direction
        for direction in DOWNWARD_FACING_DIRECTIONS
        if mission.map.is_playable_hex(neighbor(marker_position, direction))
    )


def reveal_by_movement(
    state: GameState,
    *,
    destination: HexCoord,
    rng: DeterministicRNG,
) -> RevealResolution:
    """Reveal every unresolved marker adjacent to ``destination``."""

    marker_ids = movement_reveal_marker_ids(state, destination)
    if not marker_ids:
        return RevealResolution(
            german_units=state.german_units,
            unresolved_markers=state.unresolved_markers,
            revealed_marker_ids=(),
        )

    german_units = dict(state.german_units)
    unresolved_markers = dict(state.unresolved_markers)

    for marker_id in marker_ids:
        marker_state = unresolved_markers.pop(marker_id)
        facing = facing_toward_adjacent_hex(marker_state.position, destination)
        german_units[marker_id] = RevealedGermanUnitState(
            unit_id=marker_id,
            unit_class=sample_reveal_unit_class(state.mission, rng),
            position=marker_state.position,
            facing=facing,
            status=GermanUnitStatus.ACTIVE,
        )

    return RevealResolution(
        german_units=german_units,
        unresolved_markers=unresolved_markers,
        revealed_marker_ids=marker_ids,
    )


def reveal_by_scout(
    state: GameState,
    *,
    marker_id: str,
    facing: HexDirection,
    rng: DeterministicRNG,
) -> RevealResolution:
    """Reveal exactly one marker via Scout using the chosen facing."""

    marker_state = state.unresolved_markers[marker_id]
    german_units = dict(state.german_units)
    unresolved_markers = dict(state.unresolved_markers)
    unresolved_markers.pop(marker_id)
    german_units[marker_id] = RevealedGermanUnitState(
        unit_id=marker_id,
        unit_class=sample_reveal_unit_class(state.mission, rng),
        position=marker_state.position,
        facing=facing,
        status=GermanUnitStatus.ACTIVE,
    )
    return RevealResolution(
        german_units=german_units,
        unresolved_markers=unresolved_markers,
        revealed_marker_ids=(marker_id,),
    )


def facing_toward_adjacent_hex(origin: HexCoord, target: HexCoord) -> HexDirection:
    """Return the facing from ``origin`` to an adjacent ``target`` hex."""

    for direction in HexDirection:
        if neighbor(origin, direction) == target:
            return direction
    raise ValueError(f"{target!r} is not adjacent to {origin!r}")


__all__ = [
    "DOWNWARD_FACING_DIRECTIONS",
    "RevealResolution",
    "facing_toward_adjacent_hex",
    "legal_scout_facing_directions",
    "movement_reveal_marker_ids",
    "reveal_by_movement",
    "reveal_by_scout",
    "sample_reveal_unit_class",
]
