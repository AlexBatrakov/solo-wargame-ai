from __future__ import annotations

import tomllib
from copy import deepcopy
from dataclasses import replace
from pathlib import Path

import pytest

from solo_wargame_ai.domain.hexgrid import HexCoord
from solo_wargame_ai.domain.mission import (
    BritishUnitDefinition,
    EnemyRevealTableRow,
    HiddenMarker,
)
from solo_wargame_ai.domain.validation import MissionValidationError, validate_mission
from solo_wargame_ai.io.mission_loader import load_mission, load_mission_from_data

MISSION_PATH = (
    Path(__file__).resolve().parents[1]
    / "configs"
    / "missions"
    / "mission_01_secure_the_woods_1.toml"
)
MISSION_02_PATH = (
    Path(__file__).resolve().parents[1]
    / "configs"
    / "missions"
    / "mission_02_secure_the_woods_2.toml"
)


def test_loader_rejects_unknown_terrain_name() -> None:
    mission_data = _load_raw_mission_data()
    mission_data["map"]["hexes"][0]["terrain"] = "bog"

    with pytest.raises(MissionValidationError) as exc_info:
        load_mission_from_data(mission_data)

    _assert_issue_present(exc_info.value, "map.hexes[0].terrain", "Unknown terrain type: bog")


def test_loader_rejects_unknown_top_level_schema_key() -> None:
    mission_data = _load_raw_mission_data()
    mission_data["unexpected_top_level_key"] = "oops"

    with pytest.raises(MissionValidationError) as exc_info:
        load_mission_from_data(mission_data)

    _assert_issue_present(exc_info.value, "unexpected_top_level_key", "unknown field")


def test_loader_rejects_unknown_nested_schema_key() -> None:
    mission_data = _load_raw_mission_data()
    mission_data["turns"]["bonus_turn"] = True

    with pytest.raises(MissionValidationError) as exc_info:
        load_mission_from_data(mission_data)

    _assert_issue_present(exc_info.value, "turns.bonus_turn", "unknown field")


def test_loader_reports_missing_required_field_structurally() -> None:
    mission_data = _load_raw_mission_data()
    del mission_data["map"]["coordinate_system"]

    with pytest.raises(MissionValidationError) as exc_info:
        load_mission_from_data(mission_data)

    _assert_issue_present(
        exc_info.value,
        "map.coordinate_system",
        "missing required field",
    )


def test_loader_rejects_unsupported_multi_terrain_combinations() -> None:
    mission_data = _load_raw_mission_data()
    mission_data["map"]["hexes"][0]["terrain"] = ["woods", "building"]

    with pytest.raises(MissionValidationError) as exc_info:
        load_mission_from_data(mission_data)

    _assert_issue_present(
        exc_info.value,
        "map.hexes",
        "unsupported multi-terrain combination",
    )


def test_loader_rejects_unknown_forward_direction_name() -> None:
    mission_data = _load_raw_mission_data()
    mission_data["map"]["forward_directions"][1] = "north"

    with pytest.raises(MissionValidationError) as exc_info:
        load_mission_from_data(mission_data)

    _assert_issue_present(
        exc_info.value,
        "map.forward_directions[1]",
        "Unknown hex direction: north",
    )


@pytest.mark.parametrize(
    ("mutate", "path_fragment", "message_fragment"),
    [
        (
            lambda data: data["turns"].__setitem__("turn_limit", 0),
            "turns.turn_limit",
            "turn_limit must be at least 1",
        ),
        (
            lambda data: data["british_unit_classes"]["rifle_squad"]["attacks"]["fire"].__setitem__(
                "base_to_hit",
                -99,
            ),
            "british.unit_classes.rifle_squad.attacks.fire.base_to_hit",
            "base_to_hit must be between 2 and 12",
        ),
        (
            lambda data: data["german_unit_classes"]["heavy_machine_gun"].__setitem__(
                "attack_to_hit",
                -5,
            ),
            "german.unit_classes.heavy_machine_gun.attack_to_hit",
            "attack_to_hit must be between 2 and 12",
        ),
        (
            lambda data: data["enemy_reveal_table"][0].__setitem__("roll_min", 0),
            "german.reveal_table[0].roll_min",
            "roll_min must be between 1 and 6",
        ),
        (
            lambda data: data["combat_modifiers"].__setitem__("defender_in_woods", -1),
            "combat_modifiers.defender_in_woods",
            "must be non-negative",
        ),
        (
            lambda data: data["combat_modifiers"].__setitem__("attacker_from_hill", 1),
            "combat_modifiers.attacker_from_hill",
            "must be non-positive",
        ),
    ],
)
def test_loader_rejects_invalid_numeric_domains(
    mutate,
    path_fragment: str,
    message_fragment: str,
) -> None:
    mission_data = _load_raw_mission_data()
    mutate(mission_data)

    with pytest.raises(MissionValidationError) as exc_info:
        load_mission_from_data(mission_data)

    _assert_issue_present(exc_info.value, path_fragment, message_fragment)


def test_loader_rejects_unsupported_multi_start_missions_before_runtime_init() -> None:
    mission_data = _load_raw_mission_data()
    mission_data["map"]["start_hexes"].append({"q": -1, "r": 3})

    with pytest.raises(MissionValidationError) as exc_info:
        load_mission_from_data(mission_data)

    _assert_issue_present(
        exc_info.value,
        "map.start_hexes",
        "exactly one start hex",
    )


def test_validate_mission_rejects_duplicate_unit_ids() -> None:
    mission = _load_valid_mission()
    broken_british = replace(
        mission.british,
        roster=mission.british.roster
        + (BritishUnitDefinition(unit_id="rifle_squad_a", unit_class="rifle_squad"),),
    )

    with pytest.raises(MissionValidationError) as exc_info:
        validate_mission(replace(mission, british=broken_british))

    _assert_issue_present(exc_info.value, "british.roster", "duplicate unit id 'rifle_squad_a'")


def test_validate_mission_rejects_duplicate_hidden_marker_ids() -> None:
    mission = _load_valid_mission()
    broken_map = replace(
        mission.map,
        hidden_markers=mission.map.hidden_markers
        + (HiddenMarker(marker_id="qm_1", coord=HexCoord(-1, 2)),),
    )

    with pytest.raises(MissionValidationError) as exc_info:
        validate_mission(replace(mission, map=broken_map))

    _assert_issue_present(
        exc_info.value,
        "map.hidden_markers",
        "duplicate hidden marker id 'qm_1'",
    )


def test_validate_mission_rejects_missing_orders_chart_rows() -> None:
    mission = _load_valid_mission()
    rifle_chart = mission.british.orders_charts_by_unit_class["rifle_squad"]
    shortened_chart = replace(
        rifle_chart,
        rows=tuple(row for row in rifle_chart.rows if row.die_value != 6),
    )
    broken_british = replace(mission.british, orders_charts=(shortened_chart,))

    with pytest.raises(MissionValidationError) as exc_info:
        validate_mission(replace(mission, british=broken_british))

    _assert_issue_present(
        exc_info.value,
        "british.orders.rifle_squad",
        "missing Orders Chart row for die value 6",
    )


@pytest.mark.parametrize(
    ("reveal_table", "expected_message"),
    [
        (
            (
                EnemyRevealTableRow(roll_min=1, roll_max=2, result_unit_class="heavy_machine_gun"),
                EnemyRevealTableRow(roll_min=4, roll_max=6, result_unit_class="light_machine_gun"),
            ),
            "reveal-table gap for rolls 3-3",
        ),
        (
            (
                EnemyRevealTableRow(roll_min=1, roll_max=3, result_unit_class="heavy_machine_gun"),
                EnemyRevealTableRow(roll_min=3, roll_max=6, result_unit_class="light_machine_gun"),
            ),
            "reveal-table overlap at rolls 3-3",
        ),
    ],
)
def test_validate_mission_rejects_reveal_table_gaps_and_overlaps(
    reveal_table: tuple[EnemyRevealTableRow, ...],
    expected_message: str,
) -> None:
    mission = _load_valid_mission()
    broken_german = replace(mission.german, reveal_table=reveal_table)

    with pytest.raises(MissionValidationError) as exc_info:
        validate_mission(replace(mission, german=broken_german))

    _assert_issue_present(exc_info.value, "german.reveal_table", expected_message)


def test_validate_mission_rejects_hidden_markers_on_non_playable_hexes() -> None:
    mission = _load_valid_mission()
    broken_map = replace(
        mission.map,
        hidden_markers=(HiddenMarker(marker_id="qm_1", coord=HexCoord(9, 9)),),
    )

    with pytest.raises(MissionValidationError) as exc_info:
        validate_mission(replace(mission, map=broken_map))

    _assert_issue_present(
        exc_info.value,
        "map.hidden_markers",
        "hidden marker 'qm_1' is on non-playable hex (9, 9)",
    )


def test_validate_mission_rejects_start_hexes_on_non_playable_hexes() -> None:
    mission = _load_valid_mission()
    broken_map = replace(mission.map, start_hexes=(HexCoord(9, 9),))

    with pytest.raises(MissionValidationError) as exc_info:
        validate_mission(replace(mission, map=broken_map))

    _assert_issue_present(
        exc_info.value,
        "map.start_hexes",
        "start hex (9, 9) is not playable",
    )


def test_load_mission_02_from_data_keeps_tracked_config_valid() -> None:
    mission_data = _load_raw_mission_data(MISSION_02_PATH)

    mission = load_mission_from_data(mission_data)

    assert mission.mission_id == "mission_02_secure_the_woods_2"
    assert mission.turns.turn_limit == 5
    assert len(mission.map.hidden_markers) == 2


def _load_raw_mission_data(path: Path = MISSION_PATH) -> dict[str, object]:
    with path.open("rb") as handle:
        return deepcopy(tomllib.load(handle))


def _load_valid_mission():
    return load_mission(MISSION_PATH)


def _assert_issue_present(
    error: MissionValidationError,
    path_fragment: str,
    message_fragment: str,
) -> None:
    issue_strings = [str(issue) for issue in error.issues]
    assert any(
        path_fragment in issue_string and message_fragment in issue_string
        for issue_string in issue_strings
    ), issue_strings
