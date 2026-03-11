"""Mission loader for static mission data."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any, Callable, Mapping, TypeVar

from solo_wargame_ai.domain.enums import (
    coordinate_system_from_name,
    hex_direction_from_name,
)
from solo_wargame_ai.domain.hexgrid import HexCoord
from solo_wargame_ai.domain.mission import (
    AttackProfile,
    BritishMissionData,
    BritishUnitClass,
    BritishUnitDefinition,
    CombatModifiers,
    EnemyRevealTableRow,
    GermanMissionData,
    GermanUnitClass,
    HiddenMarker,
    MapHex,
    Mission,
    MissionMap,
    MissionObjective,
    MissionSource,
    MissionTurns,
    OrdersChart,
    OrdersChartRow,
    attack_range_from_name,
    mission_objective_kind_from_name,
    order_name_from_name,
)
from solo_wargame_ai.domain.terrain import TerrainType, terrain_from_name
from solo_wargame_ai.domain.validation import ValidationCollector, validate_mission

from .mission_schema import MissionSchema, parse_mission_schema

ParsedValue = TypeVar("ParsedValue")


def load_mission(path: str | Path) -> Mission:
    """Load, materialize, and validate a mission TOML file."""

    mission_path = Path(path)
    with mission_path.open("rb") as handle:
        mission_data = tomllib.load(handle)

    return load_mission_from_data(mission_data)


def load_mission_from_data(data: Mapping[str, Any]) -> Mission:
    """Load a mission from already-parsed TOML data."""

    return build_mission(parse_mission_schema(data))


def build_mission(schema: MissionSchema) -> Mission:
    """Convert raw schema objects into the typed domain mission model."""

    collector = ValidationCollector()

    coordinate_system = _parse_name(
        schema.map.coordinate_system,
        "map.coordinate_system",
        coordinate_system_from_name,
        collector,
    )

    forward_directions = tuple(
        direction
        for index, direction_name in enumerate(schema.map.forward_directions)
        if (
            direction := _parse_name(
                direction_name,
                f"map.forward_directions[{index}]",
                hex_direction_from_name,
                collector,
            )
        )
        is not None
    )

    playable_hexes: list[MapHex] = []
    for index, hex_schema in enumerate(schema.map.hexes):
        terrain_features = _parse_terrain_features(
            hex_schema.terrain,
            path=f"map.hexes[{index}].terrain",
            collector=collector,
        )
        if terrain_features is None:
            continue

        playable_hexes.append(
            MapHex(
                hex_id=hex_schema.hex_id,
                coord=HexCoord(q=hex_schema.q, r=hex_schema.r),
                terrain_features=terrain_features,
            ),
        )

    british_unit_classes: list[BritishUnitClass] = []
    for unit_class_schema in schema.british_unit_classes:
        attacks: list[AttackProfile] = []
        for attack_schema in unit_class_schema.attacks:
            attack_range = _parse_name(
                attack_schema.range,
                f"british_unit_classes.{unit_class_schema.unit_class}.attacks.{attack_schema.attack_id}.range",
                attack_range_from_name,
                collector,
            )
            if attack_range is None:
                continue

            attacks.append(
                AttackProfile(
                    attack_id=attack_schema.attack_id,
                    attack_name=attack_schema.attack_name,
                    base_to_hit=attack_schema.base_to_hit,
                    range=attack_range,
                    uses_standard_modifiers=attack_schema.uses_standard_modifiers,
                ),
            )

        british_unit_classes.append(
            BritishUnitClass(
                unit_class=unit_class_schema.unit_class,
                display_name=unit_class_schema.display_name,
                attacks=tuple(attacks),
            ),
        )

    british_orders: list[OrdersChart] = []
    for chart_schema in schema.british_orders:
        rows: list[OrdersChartRow] = []
        for row_schema in chart_schema.rows:
            parsed_orders: list = []
            for order_index, order_name in enumerate(row_schema.orders):
                order = _parse_name(
                    order_name,
                    f"british_orders.{chart_schema.unit_class}.{row_schema.die_value}[{order_index}]",
                    order_name_from_name,
                    collector,
                )
                if order is not None:
                    parsed_orders.append(order)

            if len(parsed_orders) != len(row_schema.orders):
                continue

            rows.append(
                OrdersChartRow(
                    die_value=row_schema.die_value,
                    orders=(parsed_orders[0], parsed_orders[1]),
                ),
            )

        british_orders.append(OrdersChart(unit_class=chart_schema.unit_class, rows=tuple(rows)))

    german_unit_classes = tuple(
        GermanUnitClass(
            unit_class=unit_class_schema.unit_class,
            display_name=unit_class_schema.display_name,
            attack_to_hit=unit_class_schema.attack_to_hit,
            uses_fire_zone=unit_class_schema.uses_fire_zone,
        )
        for unit_class_schema in schema.german_unit_classes
    )

    objective_kind = _parse_name(
        schema.objective.kind,
        "objective.kind",
        mission_objective_kind_from_name,
        collector,
    )

    collector.raise_if_any()

    mission = Mission(
        schema_version=schema.schema_version,
        mission_id=schema.mission_id,
        name=schema.name,
        source=MissionSource(
            rulebook_path=schema.source.rulebook_path,
            briefing_page=schema.source.briefing_page,
            map_page=schema.source.map_page,
        ),
        turns=MissionTurns(
            turn_limit=schema.turns.turn_limit,
            first_turn_already_marked=schema.turns.first_turn_already_marked,
        ),
        objective=MissionObjective(
            kind=objective_kind,
            description=schema.objective.description,
        ),
        map=MissionMap(
            coordinate_system=coordinate_system,
            forward_directions=forward_directions,
            hexes=tuple(playable_hexes),
            start_hexes=tuple(
                HexCoord(q=hex_schema.q, r=hex_schema.r)
                for hex_schema in schema.map.start_hexes
            ),
            hidden_markers=tuple(
                HiddenMarker(
                    marker_id=marker_schema.marker_id,
                    coord=HexCoord(q=marker_schema.q, r=marker_schema.r),
                )
                for marker_schema in schema.map.hidden_markers
            ),
        ),
        british=BritishMissionData(
            roster=tuple(
                BritishUnitDefinition(
                    unit_id=unit_schema.unit_id,
                    unit_class=unit_schema.unit_class,
                )
                for unit_schema in schema.british_units
            ),
            unit_classes=tuple(british_unit_classes),
            orders_charts=tuple(british_orders),
        ),
        german=GermanMissionData(
            unit_classes=german_unit_classes,
            reveal_table=tuple(
                EnemyRevealTableRow(
                    roll_min=row_schema.roll_min,
                    roll_max=row_schema.roll_max,
                    result_unit_class=row_schema.result_unit_class,
                )
                for row_schema in schema.enemy_reveal_table
            ),
        ),
        combat_modifiers=CombatModifiers(
            defender_in_woods=schema.combat_modifiers.defender_in_woods,
            defender_in_building=schema.combat_modifiers.defender_in_building,
            attacker_from_hill=schema.combat_modifiers.attacker_from_hill,
            attacker_outside_target_fire_zone=(
                schema.combat_modifiers.attacker_outside_target_fire_zone
            ),
            per_other_british_unit_adjacent_to_target=(
                schema.combat_modifiers.per_other_british_unit_adjacent_to_target
            ),
        ),
    )
    validate_mission(mission)
    return mission


def _parse_name(
    raw_name: str,
    path: str,
    parser: Callable[[str], ParsedValue],
    collector: ValidationCollector,
) -> ParsedValue | None:
    try:
        return parser(raw_name)
    except ValueError as exc:
        collector.add(path, str(exc))
        return None


def _parse_terrain_features(
    raw_names: tuple[str, ...],
    *,
    path: str,
    collector: ValidationCollector,
) -> tuple[TerrainType, ...] | None:
    parsed_features: list[TerrainType] = []
    for index, raw_name in enumerate(raw_names):
        terrain_path = path if len(raw_names) == 1 else f"{path}[{index}]"
        terrain = _parse_name(
            raw_name,
            terrain_path,
            terrain_from_name,
            collector,
        )
        if terrain is None:
            return None
        parsed_features.append(terrain)
    return tuple(parsed_features)


__all__ = ["build_mission", "load_mission", "load_mission_from_data"]
