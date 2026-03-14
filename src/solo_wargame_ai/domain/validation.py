"""Validation helpers for static mission data and mission configs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .mission import Mission
from .terrain import TerrainType

MISSION_D6_MIN = 1
MISSION_D6_MAX = 6
MISSION_2D6_TOTAL_MIN = 2
MISSION_2D6_TOTAL_MAX = 12


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    """One validation issue with a location and human-readable message."""

    path: str
    message: str

    def __str__(self) -> str:
        return f"{self.path}: {self.message}"


class MissionValidationError(ValueError):
    """Raised when mission config or mission data fails validation."""

    def __init__(self, issues: Iterable[ValidationIssue]) -> None:
        issue_tuple = tuple(issues)
        if not issue_tuple:
            raise ValueError("MissionValidationError requires at least one issue")

        self.issues = issue_tuple
        super().__init__("; ".join(str(issue) for issue in issue_tuple))


class ValidationCollector:
    """Collect validation issues before raising a single aggregated error."""

    def __init__(self) -> None:
        self._issues: list[ValidationIssue] = []

    @property
    def issues(self) -> tuple[ValidationIssue, ...]:
        return tuple(self._issues)

    def add(self, path: str, message: str) -> None:
        self._issues.append(ValidationIssue(path=path, message=message))

    def extend(self, issues: Iterable[ValidationIssue]) -> None:
        self._issues.extend(issues)

    def raise_if_any(self) -> None:
        if self._issues:
            raise MissionValidationError(self._issues)


def validate_mission(mission: Mission) -> None:
    """Validate cross-field invariants for a static mission definition."""

    collector = ValidationCollector()

    _validate_map(mission, collector)
    _validate_numeric_domains(mission, collector)
    _validate_british_data(mission, collector)
    _validate_german_data(mission, collector)

    collector.raise_if_any()


def _validate_map(mission: Mission, collector: ValidationCollector) -> None:
    hex_id_to_coords: dict[str, list[str]] = {}
    coord_to_hex_ids: dict[tuple[int, int], list[str]] = {}
    for hex_definition in mission.map.hexes:
        _validate_map_hex_terrain(hex_definition.terrain_features, hex_definition.hex_id, collector)
        hex_id_to_coords.setdefault(hex_definition.hex_id, []).append(
            f"({hex_definition.coord.q}, {hex_definition.coord.r})",
        )
        coord_to_hex_ids.setdefault(
            (hex_definition.coord.q, hex_definition.coord.r),
            [],
        ).append(hex_definition.hex_id)

    for hex_id, coords in hex_id_to_coords.items():
        if len(coords) > 1:
            collector.add("map.hexes", f"duplicate playable hex id {hex_id!r}")

    for q_r, hex_ids in coord_to_hex_ids.items():
        if len(hex_ids) > 1:
            collector.add(
                "map.hexes",
                f"duplicate playable hex coordinate {q_r!r} used by {hex_ids!r}",
            )

    marker_ids: dict[str, int] = {}
    for marker in mission.map.hidden_markers:
        marker_ids[marker.marker_id] = marker_ids.get(marker.marker_id, 0) + 1
        if not mission.map.is_playable_hex(marker.coord):
            collector.add(
                "map.hidden_markers",
                f"hidden marker {marker.marker_id!r} is on non-playable hex "
                f"({marker.coord.q}, {marker.coord.r})",
            )

    for marker_id, count in marker_ids.items():
        if count > 1:
            collector.add("map.hidden_markers", f"duplicate hidden marker id {marker_id!r}")

    for start_hex in mission.map.start_hexes:
        if not mission.map.is_playable_hex(start_hex):
            collector.add(
                "map.start_hexes",
                f"start hex ({start_hex.q}, {start_hex.r}) is not playable",
            )

    if len(mission.map.start_hexes) != 1:
        collector.add(
            "map.start_hexes",
            "current supported missions require exactly one start hex",
        )

    if len(mission.map.forward_directions) != len(set(mission.map.forward_directions)):
        collector.add("map.forward_directions", "forward directions must be unique")


def _validate_map_hex_terrain(
    terrain_features: tuple[TerrainType, ...],
    hex_id: str,
    collector: ValidationCollector,
) -> None:
    if len(terrain_features) != len(set(terrain_features)):
        collector.add("map.hexes", f"hex {hex_id!r} repeats terrain features")

    if TerrainType.CLEAR in terrain_features and len(terrain_features) > 1:
        collector.add(
            "map.hexes",
            f"hex {hex_id!r} may not combine clear terrain with other features",
        )

    if len(terrain_features) <= 1:
        return

    supported_combo = frozenset({TerrainType.WOODS, TerrainType.HILL})
    if frozenset(terrain_features) != supported_combo:
        collector.add(
            "map.hexes",
            "unsupported multi-terrain combination "
            f"{tuple(feature.value for feature in terrain_features)!r} on hex {hex_id!r}",
        )


def _validate_british_data(mission: Mission, collector: ValidationCollector) -> None:
    unit_ids: dict[str, int] = {}
    used_unit_classes: set[str] = set()
    for unit in mission.british.roster:
        unit_ids[unit.unit_id] = unit_ids.get(unit.unit_id, 0) + 1
        used_unit_classes.add(unit.unit_class)

    for unit_id, count in unit_ids.items():
        if count > 1:
            collector.add("british.roster", f"duplicate unit id {unit_id!r}")

    for unit_class in used_unit_classes:
        if unit_class not in mission.british.unit_classes_by_name:
            collector.add(
                "british.unit_classes",
                f"missing British unit-class data for {unit_class!r}",
            )
        if unit_class not in mission.british.orders_charts_by_unit_class:
            collector.add(
                "british.orders",
                f"missing Orders Chart for unit class {unit_class!r}",
            )

    expected_die_values = set(range(MISSION_D6_MIN, MISSION_D6_MAX + 1))
    for chart in mission.british.orders_charts:
        row_counts: dict[int, int] = {}
        for row in chart.rows:
            row_counts[row.die_value] = row_counts.get(row.die_value, 0) + 1

        for die_value, count in row_counts.items():
            if count > 1:
                collector.add(
                    f"british.orders.{chart.unit_class}",
                    f"duplicate Orders Chart row for die value {die_value}",
                )

        missing_rows = sorted(expected_die_values - set(row_counts))
        for die_value in missing_rows:
            collector.add(
                f"british.orders.{chart.unit_class}",
                f"missing Orders Chart row for die value {die_value}",
            )


def _validate_numeric_domains(mission: Mission, collector: ValidationCollector) -> None:
    if mission.turns.turn_limit < 1:
        collector.add("turns.turn_limit", "turn_limit must be at least 1")

    for unit_class in mission.british.unit_classes:
        for attack in unit_class.attacks:
            _validate_2d6_threshold(
                attack.base_to_hit,
                path=(
                    "british.unit_classes."
                    f"{unit_class.unit_class}.attacks.{attack.attack_id}.base_to_hit"
                ),
                field_name="base_to_hit",
                collector=collector,
            )

    for unit_class in mission.german.unit_classes:
        _validate_2d6_threshold(
            unit_class.attack_to_hit,
            path=f"german.unit_classes.{unit_class.unit_class}.attack_to_hit",
            field_name="attack_to_hit",
            collector=collector,
        )

    _validate_non_negative(
        mission.combat_modifiers.defender_in_woods,
        path="combat_modifiers.defender_in_woods",
        field_name="defender_in_woods",
        collector=collector,
    )
    _validate_non_negative(
        mission.combat_modifiers.defender_in_building,
        path="combat_modifiers.defender_in_building",
        field_name="defender_in_building",
        collector=collector,
    )
    _validate_non_positive(
        mission.combat_modifiers.attacker_from_hill,
        path="combat_modifiers.attacker_from_hill",
        field_name="attacker_from_hill",
        collector=collector,
    )
    _validate_non_positive(
        mission.combat_modifiers.attacker_outside_target_fire_zone,
        path="combat_modifiers.attacker_outside_target_fire_zone",
        field_name="attacker_outside_target_fire_zone",
        collector=collector,
    )
    _validate_non_positive(
        mission.combat_modifiers.per_other_british_unit_adjacent_to_target,
        path="combat_modifiers.per_other_british_unit_adjacent_to_target",
        field_name="per_other_british_unit_adjacent_to_target",
        collector=collector,
    )


def _validate_german_data(mission: Mission, collector: ValidationCollector) -> None:
    unit_class_names = mission.german.unit_classes_by_name
    coverage_rows = []
    can_validate_coverage = True
    for index, row in enumerate(mission.german.reveal_table):
        row_path = f"german.reveal_table[{index}]"
        if row.result_unit_class not in unit_class_names:
            collector.add(
                "german.reveal_table",
                f"unknown reveal-table unit class {row.result_unit_class!r}",
            )
        if row.roll_min < MISSION_D6_MIN or row.roll_min > MISSION_D6_MAX:
            collector.add(
                f"{row_path}.roll_min",
                f"roll_min must be between {MISSION_D6_MIN} and {MISSION_D6_MAX}",
            )
            can_validate_coverage = False
        if row.roll_max < MISSION_D6_MIN or row.roll_max > MISSION_D6_MAX:
            collector.add(
                f"{row_path}.roll_max",
                f"roll_max must be between {MISSION_D6_MIN} and {MISSION_D6_MAX}",
            )
            can_validate_coverage = False
        if row.roll_min > row.roll_max:
            collector.add(
                "german.reveal_table",
                f"invalid reveal-table row {row.roll_min}-{row.roll_max}",
            )
            can_validate_coverage = False
        if (
            MISSION_D6_MIN <= row.roll_min <= MISSION_D6_MAX
            and MISSION_D6_MIN <= row.roll_max <= MISSION_D6_MAX
            and row.roll_min <= row.roll_max
        ):
            coverage_rows.append(row)

    if not can_validate_coverage:
        return

    sorted_rows = sorted(coverage_rows, key=lambda row: (row.roll_min, row.roll_max))
    expected_next_roll = MISSION_D6_MIN
    for row in sorted_rows:
        if row.roll_min > expected_next_roll:
            collector.add(
                "german.reveal_table",
                f"reveal-table gap for rolls {expected_next_roll}-{row.roll_min - 1}",
            )
        elif row.roll_min < expected_next_roll:
            collector.add(
                "german.reveal_table",
                "reveal-table overlap at rolls "
                f"{row.roll_min}-{min(row.roll_max, expected_next_roll - 1)}",
            )

        expected_next_roll = max(expected_next_roll, row.roll_max + 1)

    if expected_next_roll <= MISSION_D6_MAX:
        collector.add(
            "german.reveal_table",
            f"reveal-table gap for rolls {expected_next_roll}-{MISSION_D6_MAX}",
        )


def _validate_2d6_threshold(
    value: int,
    *,
    path: str,
    field_name: str,
    collector: ValidationCollector,
) -> None:
    if value < MISSION_2D6_TOTAL_MIN or value > MISSION_2D6_TOTAL_MAX:
        collector.add(
            path,
            f"{field_name} must be between {MISSION_2D6_TOTAL_MIN} and {MISSION_2D6_TOTAL_MAX}",
        )


def _validate_non_negative(
    value: int,
    *,
    path: str,
    field_name: str,
    collector: ValidationCollector,
) -> None:
    if value < 0:
        collector.add(path, f"{field_name} must be non-negative")


def _validate_non_positive(
    value: int,
    *,
    path: str,
    field_name: str,
    collector: ValidationCollector,
) -> None:
    if value > 0:
        collector.add(path, f"{field_name} must be non-positive")


__all__ = [
    "MISSION_D6_MAX",
    "MISSION_D6_MIN",
    "MissionValidationError",
    "ValidationCollector",
    "ValidationIssue",
    "validate_mission",
]
