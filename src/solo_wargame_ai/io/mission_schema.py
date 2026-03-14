"""Raw TOML-backed mission schema objects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from solo_wargame_ai.domain.validation import ValidationCollector


@dataclass(frozen=True, slots=True)
class MissionSourceSchema:
    rulebook_path: str
    briefing_page: int
    map_page: int


@dataclass(frozen=True, slots=True)
class MissionTurnsSchema:
    turn_limit: int
    first_turn_already_marked: bool


@dataclass(frozen=True, slots=True)
class MissionObjectiveSchema:
    kind: str
    description: str


@dataclass(frozen=True, slots=True)
class MapHexSchema:
    hex_id: str
    q: int
    r: int
    terrain: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class StartHexSchema:
    q: int
    r: int


@dataclass(frozen=True, slots=True)
class HiddenMarkerSchema:
    marker_id: str
    q: int
    r: int


@dataclass(frozen=True, slots=True)
class MissionMapSchema:
    coordinate_system: str
    forward_directions: tuple[str, ...]
    hexes: tuple[MapHexSchema, ...]
    start_hexes: tuple[StartHexSchema, ...]
    hidden_markers: tuple[HiddenMarkerSchema, ...]


@dataclass(frozen=True, slots=True)
class BritishUnitSchema:
    unit_id: str
    unit_class: str


@dataclass(frozen=True, slots=True)
class AttackSchema:
    attack_id: str
    attack_name: str
    base_to_hit: int
    range: str
    uses_standard_modifiers: bool


@dataclass(frozen=True, slots=True)
class BritishUnitClassSchema:
    unit_class: str
    display_name: str
    attacks: tuple[AttackSchema, ...]


@dataclass(frozen=True, slots=True)
class OrdersChartRowSchema:
    die_value: int
    orders: tuple[str, str]


@dataclass(frozen=True, slots=True)
class OrdersChartSchema:
    unit_class: str
    rows: tuple[OrdersChartRowSchema, ...]


@dataclass(frozen=True, slots=True)
class GermanUnitClassSchema:
    unit_class: str
    display_name: str
    attack_to_hit: int
    uses_fire_zone: bool


@dataclass(frozen=True, slots=True)
class EnemyRevealTableRowSchema:
    roll_min: int
    roll_max: int
    result_unit_class: str


@dataclass(frozen=True, slots=True)
class CombatModifiersSchema:
    defender_in_woods: int
    defender_in_building: int
    attacker_from_hill: int
    attacker_outside_target_fire_zone: int
    per_other_british_unit_adjacent_to_target: int


@dataclass(frozen=True, slots=True)
class MissionSchema:
    schema_version: int
    mission_id: str
    name: str
    source: MissionSourceSchema
    turns: MissionTurnsSchema
    objective: MissionObjectiveSchema
    map: MissionMapSchema
    british_units: tuple[BritishUnitSchema, ...]
    british_unit_classes: tuple[BritishUnitClassSchema, ...]
    british_orders: tuple[OrdersChartSchema, ...]
    german_unit_classes: tuple[GermanUnitClassSchema, ...]
    enemy_reveal_table: tuple[EnemyRevealTableRowSchema, ...]
    combat_modifiers: CombatModifiersSchema


def parse_mission_schema(data: Mapping[str, Any]) -> MissionSchema:
    """Parse a raw TOML mapping into typed schema objects."""

    collector = ValidationCollector()
    _reject_unknown_keys(
        data,
        path="",
        expected_keys=(
            "schema_version",
            "mission_id",
            "name",
            "source",
            "turns",
            "objective",
            "map",
            "british_units",
            "british_unit_classes",
            "british_orders",
            "german_unit_classes",
            "enemy_reveal_table",
            "combat_modifiers",
        ),
        collector=collector,
    )

    source_data = _require_mapping(data, "source", collector=collector)
    turns_data = _require_mapping(data, "turns", collector=collector)
    objective_data = _require_mapping(data, "objective", collector=collector)
    map_data = _require_mapping(data, "map", collector=collector)
    british_unit_classes_data = _require_mapping(
        data,
        "british_unit_classes",
        collector=collector,
    )
    british_orders_data = _require_mapping(data, "british_orders", collector=collector)
    german_unit_classes_data = _require_mapping(
        data,
        "german_unit_classes",
        collector=collector,
    )
    combat_modifiers_data = _require_mapping(
        data,
        "combat_modifiers",
        collector=collector,
    )

    schema = MissionSchema(
        schema_version=_require_int(data, "schema_version", collector=collector),
        mission_id=_require_str(data, "mission_id", collector=collector),
        name=_require_str(data, "name", collector=collector),
        source=_parse_source_schema(source_data, collector=collector),
        turns=_parse_turns_schema(turns_data, collector=collector),
        objective=_parse_objective_schema(objective_data, collector=collector),
        map=_parse_map_schema(map_data, collector=collector),
        british_units=tuple(
            _parse_british_unit_schema(
                unit_data,
                path=f"british_units[{index}]",
                collector=collector,
            )
            for index, unit_data in enumerate(
                _require_mapping_tuple(data, "british_units", collector=collector),
            )
        ),
        british_unit_classes=tuple(
            _parse_british_unit_class_schema(
                unit_class,
                unit_class_data,
                collector=collector,
            )
            for unit_class, unit_class_data in (british_unit_classes_data or {}).items()
        ),
        british_orders=tuple(
            _parse_orders_chart_schema(
                unit_class,
                unit_class_data,
                collector=collector,
            )
            for unit_class, unit_class_data in (british_orders_data or {}).items()
        ),
        german_unit_classes=tuple(
            _parse_german_unit_class_schema(
                unit_class,
                unit_class_data,
                collector=collector,
            )
            for unit_class, unit_class_data in (german_unit_classes_data or {}).items()
        ),
        enemy_reveal_table=tuple(
            _parse_enemy_reveal_table_row_schema(
                row_data,
                path=f"enemy_reveal_table[{index}]",
                collector=collector,
            )
            for index, row_data in enumerate(
                _require_mapping_tuple(data, "enemy_reveal_table", collector=collector),
            )
        ),
        combat_modifiers=_parse_combat_modifiers_schema(
            combat_modifiers_data,
            collector=collector,
        ),
    )
    collector.raise_if_any()
    return schema


def _parse_source_schema(
    data: Mapping[str, Any] | None,
    *,
    collector: ValidationCollector,
) -> MissionSourceSchema:
    if data is None:
        return MissionSourceSchema(rulebook_path="", briefing_page=0, map_page=0)

    _reject_unknown_keys(
        data,
        path="source",
        expected_keys=("rulebook_path", "briefing_page", "map_page"),
        collector=collector,
    )
    return MissionSourceSchema(
        rulebook_path=_require_str(data, "rulebook_path", collector=collector, path="source"),
        briefing_page=_require_int(data, "briefing_page", collector=collector, path="source"),
        map_page=_require_int(data, "map_page", collector=collector, path="source"),
    )


def _parse_turns_schema(
    data: Mapping[str, Any] | None,
    *,
    collector: ValidationCollector,
) -> MissionTurnsSchema:
    if data is None:
        return MissionTurnsSchema(turn_limit=0, first_turn_already_marked=False)

    _reject_unknown_keys(
        data,
        path="turns",
        expected_keys=("turn_limit", "first_turn_already_marked"),
        collector=collector,
    )
    return MissionTurnsSchema(
        turn_limit=_require_int(data, "turn_limit", collector=collector, path="turns"),
        first_turn_already_marked=_require_bool(
            data,
            "first_turn_already_marked",
            collector=collector,
            path="turns",
        ),
    )


def _parse_objective_schema(
    data: Mapping[str, Any] | None,
    *,
    collector: ValidationCollector,
) -> MissionObjectiveSchema:
    if data is None:
        return MissionObjectiveSchema(kind="", description="")

    _reject_unknown_keys(
        data,
        path="objective",
        expected_keys=("kind", "description"),
        collector=collector,
    )
    return MissionObjectiveSchema(
        kind=_require_str(data, "kind", collector=collector, path="objective"),
        description=_require_str(data, "description", collector=collector, path="objective"),
    )


def _parse_map_schema(
    data: Mapping[str, Any] | None,
    *,
    collector: ValidationCollector,
) -> MissionMapSchema:
    if data is None:
        return MissionMapSchema(
            coordinate_system="",
            forward_directions=(),
            hexes=(),
            start_hexes=(),
            hidden_markers=(),
        )

    _reject_unknown_keys(
        data,
        path="map",
        expected_keys=(
            "coordinate_system",
            "forward_directions",
            "hexes",
            "start_hexes",
            "hidden_markers",
        ),
        collector=collector,
    )
    return MissionMapSchema(
        coordinate_system=_require_str(
            data,
            "coordinate_system",
            collector=collector,
            path="map",
        ),
        forward_directions=_require_str_tuple(
            data,
            "forward_directions",
            collector=collector,
            path="map",
        ),
        hexes=tuple(
            _parse_map_hex_schema(
                hex_data,
                path=f"map.hexes[{index}]",
                collector=collector,
            )
            for index, hex_data in enumerate(
                _require_mapping_tuple(data, "hexes", collector=collector, path="map"),
            )
        ),
        start_hexes=tuple(
            _parse_start_hex_schema(
                hex_data,
                path=f"map.start_hexes[{index}]",
                collector=collector,
            )
            for index, hex_data in enumerate(
                _require_mapping_tuple(data, "start_hexes", collector=collector, path="map"),
            )
        ),
        hidden_markers=tuple(
            _parse_hidden_marker_schema(
                marker_data,
                path=f"map.hidden_markers[{index}]",
                collector=collector,
            )
            for index, marker_data in enumerate(
                _require_mapping_tuple(data, "hidden_markers", collector=collector, path="map"),
            )
        ),
    )


def _parse_combat_modifiers_schema(
    data: Mapping[str, Any] | None,
    *,
    collector: ValidationCollector,
) -> CombatModifiersSchema:
    if data is None:
        return CombatModifiersSchema(
            defender_in_woods=0,
            defender_in_building=0,
            attacker_from_hill=0,
            attacker_outside_target_fire_zone=0,
            per_other_british_unit_adjacent_to_target=0,
        )

    _reject_unknown_keys(
        data,
        path="combat_modifiers",
        expected_keys=(
            "defender_in_woods",
            "defender_in_building",
            "attacker_from_hill",
            "attacker_outside_target_fire_zone",
            "per_other_british_unit_adjacent_to_target",
        ),
        collector=collector,
    )
    return CombatModifiersSchema(
        defender_in_woods=_require_int(
            data,
            "defender_in_woods",
            collector=collector,
            path="combat_modifiers",
        ),
        defender_in_building=_require_int(
            data,
            "defender_in_building",
            collector=collector,
            path="combat_modifiers",
        ),
        attacker_from_hill=_require_int(
            data,
            "attacker_from_hill",
            collector=collector,
            path="combat_modifiers",
        ),
        attacker_outside_target_fire_zone=_require_int(
            data,
            "attacker_outside_target_fire_zone",
            collector=collector,
            path="combat_modifiers",
        ),
        per_other_british_unit_adjacent_to_target=_require_int(
            data,
            "per_other_british_unit_adjacent_to_target",
            collector=collector,
            path="combat_modifiers",
        ),
    )


def _parse_map_hex_schema(
    data: Mapping[str, Any],
    *,
    path: str,
    collector: ValidationCollector,
) -> MapHexSchema:
    _reject_unknown_keys(
        data,
        path=path,
        expected_keys=("hex_id", "q", "r", "terrain"),
        collector=collector,
    )
    return MapHexSchema(
        hex_id=_require_str(data, "hex_id", collector=collector, path=path),
        q=_require_int(data, "q", collector=collector, path=path),
        r=_require_int(data, "r", collector=collector, path=path),
        terrain=_require_terrain_tuple(data, "terrain", collector=collector, path=path),
    )


def _parse_start_hex_schema(
    data: Mapping[str, Any],
    *,
    path: str,
    collector: ValidationCollector,
) -> StartHexSchema:
    _reject_unknown_keys(
        data,
        path=path,
        expected_keys=("q", "r"),
        collector=collector,
    )
    return StartHexSchema(
        q=_require_int(data, "q", collector=collector, path=path),
        r=_require_int(data, "r", collector=collector, path=path),
    )


def _parse_hidden_marker_schema(
    data: Mapping[str, Any],
    *,
    path: str,
    collector: ValidationCollector,
) -> HiddenMarkerSchema:
    _reject_unknown_keys(
        data,
        path=path,
        expected_keys=("marker_id", "q", "r"),
        collector=collector,
    )
    return HiddenMarkerSchema(
        marker_id=_require_str(data, "marker_id", collector=collector, path=path),
        q=_require_int(data, "q", collector=collector, path=path),
        r=_require_int(data, "r", collector=collector, path=path),
    )


def _parse_british_unit_schema(
    data: Mapping[str, Any],
    *,
    path: str,
    collector: ValidationCollector,
) -> BritishUnitSchema:
    _reject_unknown_keys(
        data,
        path=path,
        expected_keys=("unit_id", "unit_class"),
        collector=collector,
    )
    return BritishUnitSchema(
        unit_id=_require_str(data, "unit_id", collector=collector, path=path),
        unit_class=_require_str(data, "unit_class", collector=collector, path=path),
    )


def _parse_british_unit_class_schema(
    unit_class: str,
    data: Any,
    *,
    collector: ValidationCollector,
) -> BritishUnitClassSchema:
    path = f"british_unit_classes.{unit_class}"
    unit_class_data = _ensure_mapping(data, path, collector=collector)
    attacks: tuple[AttackSchema, ...] = ()
    if unit_class_data is not None:
        _reject_unknown_keys(
            unit_class_data,
            path=path,
            expected_keys=("display_name", "attacks"),
            collector=collector,
        )
        attacks_data = _require_mapping(
            unit_class_data,
            "attacks",
            collector=collector,
            path=path,
        )
        if attacks_data is not None:
            attacks = tuple(
                _parse_attack_schema(
                    attack_id,
                    attack_data,
                    collector=collector,
                    path=f"{path}.attacks.{attack_id}",
                )
                for attack_id, attack_data in attacks_data.items()
            )

    return BritishUnitClassSchema(
        unit_class=unit_class,
        display_name=_require_str(
            unit_class_data,
            "display_name",
            collector=collector,
            path=path,
        ),
        attacks=attacks,
    )


def _parse_attack_schema(
    attack_id: str,
    data: Any,
    *,
    collector: ValidationCollector,
    path: str,
) -> AttackSchema:
    attack_data = _ensure_mapping(data, path, collector=collector)
    if attack_data is not None:
        _reject_unknown_keys(
            attack_data,
            path=path,
            expected_keys=("attack_name", "base_to_hit", "range", "uses_standard_modifiers"),
            collector=collector,
        )

    return AttackSchema(
        attack_id=attack_id,
        attack_name=_require_str(attack_data, "attack_name", collector=collector, path=path),
        base_to_hit=_require_int(attack_data, "base_to_hit", collector=collector, path=path),
        range=_require_str(attack_data, "range", collector=collector, path=path),
        uses_standard_modifiers=_require_bool(
            attack_data,
            "uses_standard_modifiers",
            collector=collector,
            path=path,
        ),
    )


def _parse_orders_chart_schema(
    unit_class: str,
    data: Any,
    *,
    collector: ValidationCollector,
) -> OrdersChartSchema:
    path = f"british_orders.{unit_class}"
    chart_data = _ensure_mapping(data, path, collector=collector)

    return OrdersChartSchema(
        unit_class=unit_class,
        rows=tuple(
            _parse_orders_chart_row_schema(
                die_value,
                orders,
                collector=collector,
                path=f"{path}.{die_value}",
            )
            for die_value, orders in (chart_data or {}).items()
        ),
    )


def _parse_orders_chart_row_schema(
    die_value: Any,
    orders: Any,
    *,
    collector: ValidationCollector,
    path: str,
) -> OrdersChartRowSchema:
    if isinstance(die_value, str):
        try:
            parsed_die_value = int(die_value)
        except ValueError:
            collector.add(path, "expected an integer-compatible die value")
            parsed_die_value = 0
    elif isinstance(die_value, int) and not isinstance(die_value, bool):
        parsed_die_value = die_value
    else:
        collector.add(path, "expected an integer-compatible die value")
        parsed_die_value = 0

    return OrdersChartRowSchema(
        die_value=parsed_die_value,
        orders=_ensure_order_pair(orders, path=path, collector=collector),
    )


def _parse_german_unit_class_schema(
    unit_class: str,
    data: Any,
    *,
    collector: ValidationCollector,
) -> GermanUnitClassSchema:
    path = f"german_unit_classes.{unit_class}"
    unit_class_data = _ensure_mapping(data, path, collector=collector)
    if unit_class_data is not None:
        _reject_unknown_keys(
            unit_class_data,
            path=path,
            expected_keys=("display_name", "attack_to_hit", "uses_fire_zone"),
            collector=collector,
        )

    return GermanUnitClassSchema(
        unit_class=unit_class,
        display_name=_require_str(
            unit_class_data,
            "display_name",
            collector=collector,
            path=path,
        ),
        attack_to_hit=_require_int(
            unit_class_data,
            "attack_to_hit",
            collector=collector,
            path=path,
        ),
        uses_fire_zone=_require_bool(
            unit_class_data,
            "uses_fire_zone",
            collector=collector,
            path=path,
        ),
    )


def _parse_enemy_reveal_table_row_schema(
    data: Mapping[str, Any],
    *,
    path: str,
    collector: ValidationCollector,
) -> EnemyRevealTableRowSchema:
    _reject_unknown_keys(
        data,
        path=path,
        expected_keys=("roll_min", "roll_max", "result_unit_class"),
        collector=collector,
    )
    return EnemyRevealTableRowSchema(
        roll_min=_require_int(data, "roll_min", collector=collector, path=path),
        roll_max=_require_int(data, "roll_max", collector=collector, path=path),
        result_unit_class=_require_str(
            data,
            "result_unit_class",
            collector=collector,
            path=path,
        ),
    )


def _reject_unknown_keys(
    data: Mapping[str, Any],
    *,
    path: str,
    expected_keys: tuple[str, ...],
    collector: ValidationCollector,
) -> None:
    expected_key_set = frozenset(expected_keys)
    for key in sorted(data):
        if key not in expected_key_set:
            collector.add(_join_path(path, key), "unknown field")


def _require_mapping(
    parent: Mapping[str, Any] | None,
    key: str,
    *,
    collector: ValidationCollector,
    path: str = "",
) -> Mapping[str, Any] | None:
    if parent is None:
        return None
    if key not in parent:
        collector.add(_join_path(path, key), "missing required field")
        return None
    return _ensure_mapping(parent[key], _join_path(path, key), collector=collector)


def _ensure_mapping(
    value: Any,
    context: str,
    *,
    collector: ValidationCollector,
) -> Mapping[str, Any] | None:
    if not isinstance(value, Mapping):
        collector.add(context, "expected a mapping")
        return None
    return value


def _require_mapping_tuple(
    parent: Mapping[str, Any] | None,
    key: str,
    *,
    collector: ValidationCollector,
    path: str = "",
) -> tuple[Mapping[str, Any], ...]:
    if parent is None:
        return ()
    full_path = _join_path(path, key)
    if key not in parent:
        collector.add(full_path, "missing required field")
        return ()
    value = parent[key]
    if not isinstance(value, list):
        collector.add(full_path, "expected a list of tables")
        return ()

    result: list[Mapping[str, Any]] = []
    for index, item in enumerate(value):
        parsed_item = _ensure_mapping(
            item,
            f"{full_path}[{index}]",
            collector=collector,
        )
        if parsed_item is not None:
            result.append(parsed_item)
    return tuple(result)


def _require_str(
    parent: Mapping[str, Any] | None,
    key: str,
    *,
    collector: ValidationCollector,
    path: str = "",
) -> str:
    if parent is None:
        return ""
    full_path = _join_path(path, key)
    if key not in parent:
        collector.add(full_path, "missing required field")
        return ""
    value = parent[key]
    if not isinstance(value, str):
        collector.add(full_path, "expected a string")
        return ""
    return value


def _require_int(
    parent: Mapping[str, Any] | None,
    key: str,
    *,
    collector: ValidationCollector,
    path: str = "",
) -> int:
    if parent is None:
        return 0
    full_path = _join_path(path, key)
    if key not in parent:
        collector.add(full_path, "missing required field")
        return 0
    value = parent[key]
    if isinstance(value, bool) or not isinstance(value, int):
        collector.add(full_path, "expected an integer")
        return 0
    return value


def _require_bool(
    parent: Mapping[str, Any] | None,
    key: str,
    *,
    collector: ValidationCollector,
    path: str = "",
) -> bool:
    if parent is None:
        return False
    full_path = _join_path(path, key)
    if key not in parent:
        collector.add(full_path, "missing required field")
        return False
    value = parent[key]
    if not isinstance(value, bool):
        collector.add(full_path, "expected a boolean")
        return False
    return value


def _require_str_tuple(
    parent: Mapping[str, Any] | None,
    key: str,
    *,
    collector: ValidationCollector,
    path: str = "",
) -> tuple[str, ...]:
    if parent is None:
        return ()
    full_path = _join_path(path, key)
    if key not in parent:
        collector.add(full_path, "missing required field")
        return ()
    value = parent[key]
    if not isinstance(value, list):
        collector.add(full_path, "expected a list of strings")
        return ()

    result: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str):
            collector.add(f"{full_path}[{index}]", "expected a string")
            continue
        result.append(item)
    return tuple(result)


def _require_terrain_tuple(
    parent: Mapping[str, Any] | None,
    key: str,
    *,
    collector: ValidationCollector,
    path: str = "",
) -> tuple[str, ...]:
    if parent is None:
        return ()
    full_path = _join_path(path, key)
    if key not in parent:
        collector.add(full_path, "missing required field")
        return ()
    value = parent[key]
    if isinstance(value, str):
        return (value,)

    if not isinstance(value, list) or not value:
        collector.add(full_path, "expected a string or non-empty list of strings")
        return ()

    result: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str):
            collector.add(f"{full_path}[{index}]", "expected a string")
            continue
        result.append(item)
    return tuple(result)


def _ensure_order_pair(
    value: Any,
    *,
    path: str,
    collector: ValidationCollector,
) -> tuple[str, str]:
    if not isinstance(value, list) or len(value) != 2:
        collector.add(path, "expected exactly two order names")
        return ("", "")

    first, second = value
    if not isinstance(first, str) or not isinstance(second, str):
        if not isinstance(first, str):
            collector.add(f"{path}[0]", "expected a string")
        if not isinstance(second, str):
            collector.add(f"{path}[1]", "expected a string")
        return ("", "")
    return (first, second)


def _join_path(parent: str, key: str) -> str:
    if not parent:
        return key
    return f"{parent}.{key}"


__all__ = [
    "AttackSchema",
    "BritishUnitClassSchema",
    "BritishUnitSchema",
    "CombatModifiersSchema",
    "EnemyRevealTableRowSchema",
    "GermanUnitClassSchema",
    "HiddenMarkerSchema",
    "MapHexSchema",
    "MissionMapSchema",
    "MissionObjectiveSchema",
    "MissionSchema",
    "MissionSourceSchema",
    "MissionTurnsSchema",
    "OrdersChartRowSchema",
    "OrdersChartSchema",
    "StartHexSchema",
    "parse_mission_schema",
]
