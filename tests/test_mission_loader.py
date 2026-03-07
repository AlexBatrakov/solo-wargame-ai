from pathlib import Path

from solo_wargame_ai.domain.enums import CoordinateSystem, HexDirection
from solo_wargame_ai.domain.hexgrid import HexCoord
from solo_wargame_ai.domain.mission import AttackRange, MissionObjectiveKind, OrderName
from solo_wargame_ai.domain.terrain import TerrainType
from solo_wargame_ai.io.mission_loader import load_mission

MISSION_PATH = (
    Path(__file__).resolve().parents[1]
    / "configs"
    / "missions"
    / "mission_01_secure_the_woods_1.toml"
)


def test_load_mission_01_builds_valid_static_mission_model() -> None:
    mission = load_mission(MISSION_PATH)

    assert mission.schema_version == 1
    assert mission.mission_id == "mission_01_secure_the_woods_1"
    assert mission.name == "Mission 1 - Secure the Woods (1)"
    assert mission.source.rulebook_path == "docs/reference/rules.pdf"
    assert mission.source.briefing_page == 16
    assert mission.source.map_page == 17
    assert mission.turns.turn_limit == 4
    assert mission.turns.first_turn_already_marked is True
    assert mission.objective.kind is MissionObjectiveKind.CLEAR_ALL_HOSTILES
    assert mission.objective.description == "Reveal and clear the German unit before time runs out."

    assert mission.map.coordinate_system is CoordinateSystem.AXIAL_FLAT_TOP
    assert mission.map.forward_directions == (
        HexDirection.UP_LEFT,
        HexDirection.UP,
        HexDirection.UP_RIGHT,
    )
    assert len(mission.map.hexes) == 10
    assert mission.map.playable_hexes == frozenset(
        {
            HexCoord(0, 0),
            HexCoord(-1, 1),
            HexCoord(1, 0),
            HexCoord(0, 1),
            HexCoord(-1, 2),
            HexCoord(1, 1),
            HexCoord(0, 2),
            HexCoord(-1, 3),
            HexCoord(1, 2),
            HexCoord(0, 3),
        },
    )
    assert mission.map.hex_at(HexCoord(0, 1)) is not None
    assert mission.map.hex_at(HexCoord(0, 1)).terrain is TerrainType.WOODS
    assert mission.map.start_hexes == (HexCoord(0, 3),)
    assert mission.map.hidden_markers[0].marker_id == "qm_1"
    assert mission.map.hidden_markers[0].coord == HexCoord(0, 1)

    assert tuple(unit.unit_id for unit in mission.british.roster) == (
        "rifle_squad_a",
        "rifle_squad_b",
    )
    rifle_class = mission.british.unit_classes_by_name["rifle_squad"]
    assert rifle_class.display_name == "Rifle Squad"
    assert rifle_class.attacks_by_id["fire"].base_to_hit == 8
    assert rifle_class.attacks_by_id["fire"].range is AttackRange.ADJACENT
    assert rifle_class.attacks_by_id["fire"].uses_standard_modifiers is True
    assert rifle_class.attacks_by_id["grenade_attack"].base_to_hit == 6
    assert rifle_class.attacks_by_id["grenade_attack"].uses_standard_modifiers is False

    orders_chart = mission.british.orders_charts_by_unit_class["rifle_squad"]
    assert orders_chart.rows_by_die_value[1].orders == (
        OrderName.RALLY,
        OrderName.GRENADE_ATTACK,
    )
    assert orders_chart.rows_by_die_value[6].orders == (
        OrderName.ADVANCE,
        OrderName.FIRE,
    )

    assert mission.german.unit_classes_by_name["heavy_machine_gun"].attack_to_hit == 5
    assert mission.german.unit_classes_by_name["light_machine_gun"].attack_to_hit == 6
    assert mission.german.reveal_table[0].roll_min == 1
    assert mission.german.reveal_table[0].roll_max == 2
    assert mission.german.reveal_table[0].result_unit_class == "heavy_machine_gun"
    assert mission.german.reveal_table[1].roll_min == 3
    assert mission.german.reveal_table[1].roll_max == 6
    assert mission.german.reveal_table[1].result_unit_class == "light_machine_gun"

    assert mission.combat_modifiers.defender_in_woods == 1
    assert mission.combat_modifiers.attacker_outside_target_fire_zone == -1
    assert mission.combat_modifiers.per_other_british_unit_adjacent_to_target == -1
