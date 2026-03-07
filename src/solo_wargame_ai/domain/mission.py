"""Static mission model for scenario configuration data."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType
from typing import Mapping

from .enums import CoordinateSystem, HexDirection
from .hexgrid import HexCoord
from .terrain import TerrainType


class MissionObjectiveKind(StrEnum):
    """Machine-readable objective identifiers used by mission configs."""

    CLEAR_ALL_HOSTILES = "clear_all_hostiles"


def mission_objective_kind_from_name(name: str) -> MissionObjectiveKind:
    """Parse an objective identifier from mission/config data."""

    try:
        return MissionObjectiveKind(name)
    except ValueError as exc:
        raise ValueError(f"Unknown mission objective kind: {name}") from exc


class OrderName(StrEnum):
    """British order identifiers needed for Mission 1."""

    ADVANCE = "advance"
    FIRE = "fire"
    GRENADE_ATTACK = "grenade_attack"
    TAKE_COVER = "take_cover"
    RALLY = "rally"
    SCOUT = "scout"


def order_name_from_name(name: str) -> OrderName:
    """Parse an order identifier from mission/config data."""

    try:
        return OrderName(name)
    except ValueError as exc:
        raise ValueError(f"Unknown order name: {name}") from exc


class AttackRange(StrEnum):
    """Attack-range identifiers needed for Mission 1 attack data."""

    ADJACENT = "adjacent"


def attack_range_from_name(name: str) -> AttackRange:
    """Parse an attack-range identifier from mission/config data."""

    try:
        return AttackRange(name)
    except ValueError as exc:
        raise ValueError(f"Unknown attack range: {name}") from exc


@dataclass(frozen=True, slots=True)
class MissionSource:
    """Rulebook/source metadata for a transcribed mission."""

    rulebook_path: str
    briefing_page: int
    map_page: int


@dataclass(frozen=True, slots=True)
class MissionTurns:
    """Static turn-track metadata."""

    turn_limit: int
    first_turn_already_marked: bool


@dataclass(frozen=True, slots=True)
class MissionObjective:
    """Static objective metadata."""

    kind: MissionObjectiveKind
    description: str


@dataclass(frozen=True, slots=True)
class MapHex:
    """One playable hex defined by the mission map."""

    hex_id: str
    coord: HexCoord
    terrain: TerrainType


@dataclass(frozen=True, slots=True)
class HiddenMarker:
    """One unresolved hidden marker on the mission map."""

    marker_id: str
    coord: HexCoord


@dataclass(frozen=True, slots=True)
class MissionMap:
    """Static board transcription and setup-space information."""

    coordinate_system: CoordinateSystem
    forward_directions: tuple[HexDirection, ...]
    hexes: tuple[MapHex, ...]
    start_hexes: tuple[HexCoord, ...]
    hidden_markers: tuple[HiddenMarker, ...]
    hexes_by_coord: Mapping[HexCoord, MapHex] = field(init=False, repr=False)
    hidden_markers_by_id: Mapping[str, HiddenMarker] = field(init=False, repr=False)
    playable_hexes: frozenset[HexCoord] = field(init=False, repr=False)
    start_hex_set: frozenset[HexCoord] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "hexes_by_coord",
            MappingProxyType(
                {hex_definition.coord: hex_definition for hex_definition in self.hexes},
            ),
        )
        object.__setattr__(
            self,
            "hidden_markers_by_id",
            MappingProxyType(
                {marker.marker_id: marker for marker in self.hidden_markers},
            ),
        )
        object.__setattr__(
            self,
            "playable_hexes",
            frozenset(hex_definition.coord for hex_definition in self.hexes),
        )
        object.__setattr__(self, "start_hex_set", frozenset(self.start_hexes))

    def is_playable_hex(self, coord: HexCoord) -> bool:
        """Return whether ``coord`` belongs to the playable map."""

        return coord in self.playable_hexes

    def hex_at(self, coord: HexCoord) -> MapHex | None:
        """Return the playable-hex definition for ``coord`` if present."""

        return self.hexes_by_coord.get(coord)


@dataclass(frozen=True, slots=True)
class AttackProfile:
    """Mission-local attack data for one British attack mode."""

    attack_id: str
    attack_name: str
    base_to_hit: int
    range: AttackRange
    uses_standard_modifiers: bool


@dataclass(frozen=True, slots=True)
class BritishUnitClass:
    """Mission-local data for one British unit class."""

    unit_class: str
    display_name: str
    attacks: tuple[AttackProfile, ...]
    attacks_by_id: Mapping[str, AttackProfile] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "attacks_by_id",
            MappingProxyType({attack.attack_id: attack for attack in self.attacks}),
        )


@dataclass(frozen=True, slots=True)
class BritishUnitDefinition:
    """One British unit available in the mission setup space."""

    unit_id: str
    unit_class: str


@dataclass(frozen=True, slots=True)
class OrdersChartRow:
    """One die-result row from a mission Orders Chart."""

    die_value: int
    orders: tuple[OrderName, OrderName]

    @property
    def first_order(self) -> OrderName:
        """Return the first printed order."""

        return self.orders[0]

    @property
    def second_order(self) -> OrderName:
        """Return the second printed order."""

        return self.orders[1]


@dataclass(frozen=True, slots=True)
class OrdersChart:
    """Mission Orders Chart for one British unit class."""

    unit_class: str
    rows: tuple[OrdersChartRow, ...]
    rows_by_die_value: Mapping[int, OrdersChartRow] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "rows_by_die_value",
            MappingProxyType({row.die_value: row for row in self.rows}),
        )


@dataclass(frozen=True, slots=True)
class BritishMissionData:
    """British setup-space data for the mission."""

    roster: tuple[BritishUnitDefinition, ...]
    unit_classes: tuple[BritishUnitClass, ...]
    orders_charts: tuple[OrdersChart, ...]
    unit_classes_by_name: Mapping[str, BritishUnitClass] = field(init=False, repr=False)
    orders_charts_by_unit_class: Mapping[str, OrdersChart] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "unit_classes_by_name",
            MappingProxyType(
                {unit_class.unit_class: unit_class for unit_class in self.unit_classes},
            ),
        )
        object.__setattr__(
            self,
            "orders_charts_by_unit_class",
            MappingProxyType(
                {chart.unit_class: chart for chart in self.orders_charts},
            ),
        )


@dataclass(frozen=True, slots=True)
class GermanUnitClass:
    """Mission-local data for one German unit class."""

    unit_class: str
    display_name: str
    attack_to_hit: int
    uses_fire_zone: bool


@dataclass(frozen=True, slots=True)
class EnemyRevealTableRow:
    """One mission reveal-table interval."""

    roll_min: int
    roll_max: int
    result_unit_class: str


@dataclass(frozen=True, slots=True)
class GermanMissionData:
    """German static mission data."""

    unit_classes: tuple[GermanUnitClass, ...]
    reveal_table: tuple[EnemyRevealTableRow, ...]
    unit_classes_by_name: Mapping[str, GermanUnitClass] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "unit_classes_by_name",
            MappingProxyType(
                {unit_class.unit_class: unit_class for unit_class in self.unit_classes},
            ),
        )


@dataclass(frozen=True, slots=True)
class CombatModifiers:
    """Mission-local combat modifier values."""

    defender_in_woods: int
    attacker_outside_target_fire_zone: int
    per_other_british_unit_adjacent_to_target: int


@dataclass(frozen=True, slots=True)
class Mission:
    """Validated static mission definition."""

    schema_version: int
    mission_id: str
    name: str
    source: MissionSource
    turns: MissionTurns
    objective: MissionObjective
    map: MissionMap
    british: BritishMissionData
    german: GermanMissionData
    combat_modifiers: CombatModifiers


__all__ = [
    "AttackProfile",
    "AttackRange",
    "BritishMissionData",
    "BritishUnitClass",
    "BritishUnitDefinition",
    "CombatModifiers",
    "EnemyRevealTableRow",
    "GermanMissionData",
    "GermanUnitClass",
    "HiddenMarker",
    "MapHex",
    "Mission",
    "MissionMap",
    "MissionObjective",
    "MissionObjectiveKind",
    "MissionSource",
    "MissionTurns",
    "OrderName",
    "OrdersChart",
    "OrdersChartRow",
    "attack_range_from_name",
    "mission_objective_kind_from_name",
    "order_name_from_name",
]
