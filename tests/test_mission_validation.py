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


def test_loader_rejects_unknown_terrain_name() -> None:
    mission_data = _load_raw_mission_data()
    mission_data["map"]["hexes"][0]["terrain"] = "bog"

    with pytest.raises(MissionValidationError) as exc_info:
        load_mission_from_data(mission_data)

    _assert_issue_present(exc_info.value, "map.hexes[0].terrain", "Unknown terrain type: bog")


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


def _load_raw_mission_data() -> dict[str, object]:
    with MISSION_PATH.open("rb") as handle:
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
