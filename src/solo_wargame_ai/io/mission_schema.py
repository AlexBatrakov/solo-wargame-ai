"""Raw TOML-backed mission schema objects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


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
    terrain: str


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

    source_data = _require_mapping(data, "source")
    turns_data = _require_mapping(data, "turns")
    objective_data = _require_mapping(data, "objective")
    map_data = _require_mapping(data, "map")
    british_unit_classes_data = _require_mapping(data, "british_unit_classes")
    british_orders_data = _require_mapping(data, "british_orders")
    german_unit_classes_data = _require_mapping(data, "german_unit_classes")
    combat_modifiers_data = _require_mapping(data, "combat_modifiers")

    return MissionSchema(
        schema_version=_require_int(data, "schema_version"),
        mission_id=_require_str(data, "mission_id"),
        name=_require_str(data, "name"),
        source=MissionSourceSchema(
            rulebook_path=_require_str(source_data, "rulebook_path"),
            briefing_page=_require_int(source_data, "briefing_page"),
            map_page=_require_int(source_data, "map_page"),
        ),
        turns=MissionTurnsSchema(
            turn_limit=_require_int(turns_data, "turn_limit"),
            first_turn_already_marked=_require_bool(turns_data, "first_turn_already_marked"),
        ),
        objective=MissionObjectiveSchema(
            kind=_require_str(objective_data, "kind"),
            description=_require_str(objective_data, "description"),
        ),
        map=MissionMapSchema(
            coordinate_system=_require_str(map_data, "coordinate_system"),
            forward_directions=_require_str_tuple(map_data, "forward_directions"),
            hexes=tuple(
                _parse_map_hex_schema(hex_data)
                for hex_data in _require_mapping_tuple(map_data, "hexes")
            ),
            start_hexes=tuple(
                _parse_start_hex_schema(hex_data)
                for hex_data in _require_mapping_tuple(map_data, "start_hexes")
            ),
            hidden_markers=tuple(
                _parse_hidden_marker_schema(marker_data)
                for marker_data in _require_mapping_tuple(map_data, "hidden_markers")
            ),
        ),
        british_units=tuple(
            _parse_british_unit_schema(unit_data)
            for unit_data in _require_mapping_tuple(data, "british_units")
        ),
        british_unit_classes=tuple(
            _parse_british_unit_class_schema(unit_class, unit_class_data)
            for unit_class, unit_class_data in british_unit_classes_data.items()
        ),
        british_orders=tuple(
            _parse_orders_chart_schema(unit_class, unit_class_data)
            for unit_class, unit_class_data in british_orders_data.items()
        ),
        german_unit_classes=tuple(
            _parse_german_unit_class_schema(unit_class, unit_class_data)
            for unit_class, unit_class_data in german_unit_classes_data.items()
        ),
        enemy_reveal_table=tuple(
            _parse_enemy_reveal_table_row_schema(row_data)
            for row_data in _require_mapping_tuple(data, "enemy_reveal_table")
        ),
        combat_modifiers=CombatModifiersSchema(
            defender_in_woods=_require_int(combat_modifiers_data, "defender_in_woods"),
            attacker_outside_target_fire_zone=_require_int(
                combat_modifiers_data,
                "attacker_outside_target_fire_zone",
            ),
            per_other_british_unit_adjacent_to_target=_require_int(
                combat_modifiers_data,
                "per_other_british_unit_adjacent_to_target",
            ),
        ),
    )


def _parse_map_hex_schema(data: Mapping[str, Any]) -> MapHexSchema:
    return MapHexSchema(
        hex_id=_require_str(data, "hex_id"),
        q=_require_int(data, "q"),
        r=_require_int(data, "r"),
        terrain=_require_str(data, "terrain"),
    )


def _parse_start_hex_schema(data: Mapping[str, Any]) -> StartHexSchema:
    return StartHexSchema(
        q=_require_int(data, "q"),
        r=_require_int(data, "r"),
    )


def _parse_hidden_marker_schema(data: Mapping[str, Any]) -> HiddenMarkerSchema:
    return HiddenMarkerSchema(
        marker_id=_require_str(data, "marker_id"),
        q=_require_int(data, "q"),
        r=_require_int(data, "r"),
    )


def _parse_british_unit_schema(data: Mapping[str, Any]) -> BritishUnitSchema:
    return BritishUnitSchema(
        unit_id=_require_str(data, "unit_id"),
        unit_class=_require_str(data, "unit_class"),
    )


def _parse_british_unit_class_schema(
    unit_class: str,
    data: Any,
) -> BritishUnitClassSchema:
    unit_class_data = _ensure_mapping(data, f"british_unit_classes.{unit_class}")
    attacks_data = _require_mapping(unit_class_data, "attacks")

    return BritishUnitClassSchema(
        unit_class=unit_class,
        display_name=_require_str(unit_class_data, "display_name"),
        attacks=tuple(
            _parse_attack_schema(attack_id, attack_data)
            for attack_id, attack_data in attacks_data.items()
        ),
    )


def _parse_attack_schema(attack_id: str, data: Any) -> AttackSchema:
    attack_data = _ensure_mapping(data, f"attack {attack_id}")

    return AttackSchema(
        attack_id=attack_id,
        attack_name=_require_str(attack_data, "attack_name"),
        base_to_hit=_require_int(attack_data, "base_to_hit"),
        range=_require_str(attack_data, "range"),
        uses_standard_modifiers=_require_bool(attack_data, "uses_standard_modifiers"),
    )


def _parse_orders_chart_schema(unit_class: str, data: Any) -> OrdersChartSchema:
    chart_data = _ensure_mapping(data, f"british_orders.{unit_class}")

    return OrdersChartSchema(
        unit_class=unit_class,
        rows=tuple(
            _parse_orders_chart_row_schema(die_value, orders)
            for die_value, orders in chart_data.items()
        ),
    )


def _parse_orders_chart_row_schema(die_value: Any, orders: Any) -> OrdersChartRowSchema:
    if isinstance(die_value, str):
        parsed_die_value = int(die_value)
    elif isinstance(die_value, int) and not isinstance(die_value, bool):
        parsed_die_value = die_value
    else:
        raise TypeError(
            "Expected Orders Chart die value to be int-compatible, "
            f"got {type(die_value)!r}",
        )

    return OrdersChartRowSchema(
        die_value=parsed_die_value,
        orders=_ensure_order_pair(orders),
    )


def _parse_german_unit_class_schema(unit_class: str, data: Any) -> GermanUnitClassSchema:
    unit_class_data = _ensure_mapping(data, f"german_unit_classes.{unit_class}")

    return GermanUnitClassSchema(
        unit_class=unit_class,
        display_name=_require_str(unit_class_data, "display_name"),
        attack_to_hit=_require_int(unit_class_data, "attack_to_hit"),
        uses_fire_zone=_require_bool(unit_class_data, "uses_fire_zone"),
    )


def _parse_enemy_reveal_table_row_schema(data: Mapping[str, Any]) -> EnemyRevealTableRowSchema:
    return EnemyRevealTableRowSchema(
        roll_min=_require_int(data, "roll_min"),
        roll_max=_require_int(data, "roll_max"),
        result_unit_class=_require_str(data, "result_unit_class"),
    )


def _require_mapping(parent: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    return _ensure_mapping(parent[key], key)


def _ensure_mapping(value: Any, context: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"Expected {context} to be a mapping")
    return value


def _require_mapping_tuple(parent: Mapping[str, Any], key: str) -> tuple[Mapping[str, Any], ...]:
    value = parent[key]
    if not isinstance(value, list):
        raise TypeError(f"Expected {key} to be a list of tables")

    result: list[Mapping[str, Any]] = []
    for item in value:
        result.append(_ensure_mapping(item, key))
    return tuple(result)


def _require_str(parent: Mapping[str, Any], key: str) -> str:
    value = parent[key]
    if not isinstance(value, str):
        raise TypeError(f"Expected {key} to be a string")
    return value


def _require_int(parent: Mapping[str, Any], key: str) -> int:
    value = parent[key]
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"Expected {key} to be an integer")
    return value


def _require_bool(parent: Mapping[str, Any], key: str) -> bool:
    value = parent[key]
    if not isinstance(value, bool):
        raise TypeError(f"Expected {key} to be a boolean")
    return value


def _require_str_tuple(parent: Mapping[str, Any], key: str) -> tuple[str, ...]:
    value = parent[key]
    if not isinstance(value, list):
        raise TypeError(f"Expected {key} to be a list of strings")

    result: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise TypeError(f"Expected every entry in {key} to be a string")
        result.append(item)
    return tuple(result)


def _ensure_order_pair(value: Any) -> tuple[str, str]:
    if not isinstance(value, list) or len(value) != 2:
        raise TypeError("Expected Orders Chart row to contain exactly two order names")

    first, second = value
    if not isinstance(first, str) or not isinstance(second, str):
        raise TypeError("Expected Orders Chart row entries to be strings")
    return (first, second)


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
