from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from solo_wargame_ai.domain.decision_context import ChooseOrderExecutionContext
from solo_wargame_ai.domain.enums import HexDirection
from solo_wargame_ai.domain.hexgrid import HexCoord
from solo_wargame_ai.domain.state import (
    GameStateValidationError,
    create_initial_game_state,
    validate_game_state,
)
from solo_wargame_ai.domain.units import (
    BritishUnitState,
    GermanUnitStatus,
    RevealedGermanUnitState,
)
from solo_wargame_ai.io.mission_loader import load_mission

MISSION_PATH = (
    Path(__file__).resolve().parents[1]
    / "configs"
    / "missions"
    / "mission_01_secure_the_woods_1.toml"
)


def test_validate_game_state_rejects_runtime_units_on_non_playable_hexes() -> None:
    state = _load_valid_state()
    broken_unit = replace(state.british_units["rifle_squad_a"], position=HexCoord(9, 9))

    with pytest.raises(GameStateValidationError) as exc_info:
        validate_game_state(
            replace(
                state,
                british_units={**state.british_units, "rifle_squad_a": broken_unit},
            ),
        )

    _assert_issue_present(
        exc_info.value,
        "british_units.rifle_squad_a.position",
        "playable hex",
    )


def test_validate_game_state_rejects_british_and_german_cooccupation() -> None:
    state = _load_valid_state()
    german_unit = RevealedGermanUnitState(
        unit_id="qm_1",
        unit_class="heavy_machine_gun",
        position=HexCoord(0, 3),
        facing=HexDirection.DOWN,
        status=GermanUnitStatus.ACTIVE,
    )

    with pytest.raises(GameStateValidationError) as exc_info:
        validate_game_state(
            replace(
                state,
                german_units={"qm_1": german_unit},
                unresolved_markers={},
            ),
        )

    _assert_issue_present(exc_info.value, "occupancy", "may not occupy the same hex")


def test_validate_game_state_rejects_unresolved_marker_overlap_with_revealed_german() -> None:
    state = _load_valid_state()
    german_unit = RevealedGermanUnitState(
        unit_id="qm_1",
        unit_class="light_machine_gun",
        position=HexCoord(0, 1),
        facing=HexDirection.DOWN,
        status=GermanUnitStatus.ACTIVE,
    )

    with pytest.raises(GameStateValidationError) as exc_info:
        validate_game_state(replace(state, german_units={"qm_1": german_unit}))

    _assert_issue_present(
        exc_info.value,
        "unresolved_markers.qm_1.position",
        "may not overlap a revealed German unit",
    )


def test_validate_game_state_rejects_invalid_activated_ids() -> None:
    state = _load_valid_state()

    with pytest.raises(GameStateValidationError) as exc_info:
        validate_game_state(
            replace(state, activated_british_unit_ids=frozenset({"ghost_unit"})),
        )

    _assert_issue_present(
        exc_info.value,
        "activated_british_unit_ids",
        "does not exist in runtime state",
    )


def test_validate_game_state_rejects_pending_decision_without_required_activation() -> None:
    state = _load_valid_state()

    with pytest.raises(GameStateValidationError) as exc_info:
        validate_game_state(
            replace(
                state,
                pending_decision=ChooseOrderExecutionContext(),
                current_activation=None,
            ),
        )

    _assert_issue_present(exc_info.value, "current_activation", "required")


def test_validate_game_state_rejects_negative_cover() -> None:
    state = _load_valid_state()
    broken_unit = replace(state.british_units["rifle_squad_a"], cover=-1)

    with pytest.raises(GameStateValidationError) as exc_info:
        validate_game_state(
            replace(
                state,
                british_units={**state.british_units, "rifle_squad_a": broken_unit},
            ),
        )

    _assert_issue_present(exc_info.value, "british_units.rifle_squad_a.cover", "non-negative")


def test_validate_game_state_rejects_invalid_german_facing() -> None:
    state = _load_valid_state()
    german_unit = RevealedGermanUnitState(
        unit_id="qm_1",
        unit_class="light_machine_gun",
        position=HexCoord(0, 1),
        facing="north",  # type: ignore[arg-type]
        status=GermanUnitStatus.ACTIVE,
    )

    with pytest.raises(GameStateValidationError) as exc_info:
        validate_game_state(
            replace(
                state,
                german_units={"qm_1": german_unit},
                unresolved_markers={},
            ),
        )

    _assert_issue_present(exc_info.value, "german_units.qm_1.facing", "HexDirection")


def test_validate_game_state_rejects_runtime_british_unit_class_mismatches() -> None:
    state = _load_valid_state()
    broken_unit = BritishUnitState(
        unit_id="rifle_squad_a",
        unit_class="heavy_machine_gun",
        position=HexCoord(0, 3),
        morale=state.british_units["rifle_squad_a"].morale,
        cover=0,
    )

    with pytest.raises(GameStateValidationError) as exc_info:
        validate_game_state(
            replace(
                state,
                british_units={**state.british_units, "rifle_squad_a": broken_unit},
            ),
        )

    _assert_issue_present(
        exc_info.value,
        "british_units.rifle_squad_a.unit_class",
        "must match the attached Mission roster",
    )


def _load_valid_state():
    mission = load_mission(MISSION_PATH)
    return create_initial_game_state(mission)


def _assert_issue_present(
    error: GameStateValidationError,
    path_fragment: str,
    message_fragment: str,
) -> None:
    issue_strings = [str(issue) for issue in error.issues]
    assert any(
        path_fragment in issue_string and message_fragment in issue_string
        for issue_string in issue_strings
    ), issue_strings
