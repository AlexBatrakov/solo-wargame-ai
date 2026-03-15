from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from solo_wargame_ai.domain.actions import (
    ChooseOrderExecutionAction,
    OrderExecutionChoice,
    SelectActivationDieAction,
    SelectBritishUnitAction,
)
from solo_wargame_ai.domain.decision_context import ChooseGermanUnitContext
from solo_wargame_ai.domain.enums import HexDirection
from solo_wargame_ai.domain.hexgrid import HexCoord
from solo_wargame_ai.domain.resolver import apply_action
from solo_wargame_ai.domain.state import GamePhase, create_initial_game_state
from solo_wargame_ai.domain.units import GermanUnitStatus, RevealedGermanUnitState
from solo_wargame_ai.env.legal_action_mask import build_legal_action_selection
from solo_wargame_ai.env.mission3_action_catalog import (
    build_mission3_action_catalog,
    build_mission3_contact_handle_map,
)
from solo_wargame_ai.env.mission3_observation import build_mission3_observation
from solo_wargame_ai.env.normalized_state import normalize_env_state
from solo_wargame_ai.io.mission_loader import load_mission

MISSION_PATH = (
    Path(__file__).resolve().parents[1]
    / "configs"
    / "missions"
    / "mission_03_secure_the_building.toml"
)


def test_mission3_observation_and_legality_share_the_same_normalized_state_boundary() -> None:
    mission = load_mission(MISSION_PATH)
    catalog = build_mission3_action_catalog(mission)
    contact_handles = build_mission3_contact_handle_map(mission)
    base_state = create_initial_game_state(mission, seed=0)
    raw_state = replace(
        base_state,
        phase=GamePhase.GERMAN,
        activated_british_unit_ids=frozenset(base_state.british_units),
        activated_german_unit_ids=frozenset(),
        pending_decision=ChooseGermanUnitContext(),
        current_activation=None,
    )

    normalized_state = normalize_env_state(raw_state)
    observation = build_mission3_observation(normalized_state, contact_handles)
    legal_selection = build_legal_action_selection(normalized_state, catalog)

    assert raw_state.phase is GamePhase.GERMAN
    assert normalized_state.state.phase is GamePhase.BRITISH
    assert normalized_state.state.turn == 2
    assert observation["phase"] == "british"
    assert observation["turn"] == 2
    assert observation["decision"]["pending_kind"] == "choose_british_unit"
    assert legal_selection.legal_action_ids == (0, 1, 2)


def test_mission3_observation_stays_serializable_and_keeps_public_multi_terrain_data() -> None:
    mission = load_mission(MISSION_PATH)
    contact_handles = build_mission3_contact_handle_map(mission)
    normalized_state = normalize_env_state(_advance_parameter_state())

    observation = build_mission3_observation(normalized_state, contact_handles)

    wooded_hill_hex = _find_hex_payload(observation, HexCoord(1, 0))
    building_hex = _find_hex_payload(observation, HexCoord(0, 1))

    assert wooded_hill_hex == {
        "hex_id": "upper_right_wooded_hill",
        "coord": {"q": 1, "r": 0},
        "terrain_features": ["woods", "hill"],
        "is_start_hex": False,
    }
    assert building_hex == {
        "hex_id": "building_hex",
        "coord": {"q": 0, "r": 1},
        "terrain_features": ["building"],
        "is_start_hex": False,
    }
    assert observation["decision"] == {
        "pending_kind": "choose_order_parameter",
        "pending_order": {
            "order": "advance",
            "order_index": 0,
        },
        "current_activation": {
            "active_unit_id": "rifle_squad_c",
            "roll": [2, 5],
            "selected_die": 2,
            "planned_orders": ["advance"],
            "next_order_index": 0,
            "active_order": "advance",
        },
    }
    assert observation["unresolved_markers"] == [
        {"contact_id": "contact_0", "position": {"q": -1, "r": 2}},
        {"contact_id": "contact_1", "position": {"q": 0, "r": 1}},
        {"contact_id": "contact_2", "position": {"q": 1, "r": 1}},
    ]
    assert observation["revealed_german_units"] == []
    _assert_simple_serializable(observation)
    _assert_no_raw_qm_strings(observation)


def test_mission3_observation_uses_contact_ids_for_revealed_german_units() -> None:
    mission = load_mission(MISSION_PATH)
    contact_handles = build_mission3_contact_handle_map(mission)
    normalized_state = normalize_env_state(_revealed_contact_state())

    observation = build_mission3_observation(normalized_state, contact_handles)

    assert observation["revealed_german_units"] == [
        {
            "contact_id": "contact_1",
            "unit_class": "light_machine_gun",
            "position": {"q": 0, "r": 1},
            "facing": "down",
            "status": "active",
            "activated_this_phase": False,
        },
    ]
    assert observation["unresolved_markers"] == [
        {"contact_id": "contact_0", "position": {"q": -1, "r": 2}},
        {"contact_id": "contact_2", "position": {"q": 1, "r": 1}},
    ]
    assert "unit_id" not in observation["revealed_german_units"][0]
    assert "marker_id" not in observation["unresolved_markers"][0]
    _assert_no_raw_qm_strings(observation)


def _advance_parameter_state():
    mission = load_mission(MISSION_PATH)
    state = create_initial_game_state(mission, seed=1)
    state = apply_action(state, SelectBritishUnitAction(unit_id="rifle_squad_c"))
    state = apply_action(state, SelectActivationDieAction(die_value=2))
    return apply_action(
        state,
        ChooseOrderExecutionAction(choice=OrderExecutionChoice.FIRST_ORDER_ONLY),
    )


def _revealed_contact_state():
    mission = load_mission(MISSION_PATH)
    base_state = create_initial_game_state(mission, seed=0)
    unresolved_markers = dict(base_state.unresolved_markers)
    unresolved_markers.pop("qm_2")
    return replace(
        base_state,
        german_units={
            "qm_2": RevealedGermanUnitState(
                unit_id="qm_2",
                unit_class="light_machine_gun",
                position=HexCoord(0, 1),
                facing=HexDirection.DOWN,
                status=GermanUnitStatus.ACTIVE,
            ),
        },
        unresolved_markers=unresolved_markers,
    )


def _find_hex_payload(observation: dict[str, object], coord: HexCoord) -> dict[str, object]:
    for hex_payload in observation["mission"]["hexes"]:
        if hex_payload["coord"] == {"q": coord.q, "r": coord.r}:
            return hex_payload
    raise AssertionError(f"Missing hex payload for {coord!r}")


def _assert_simple_serializable(value: object) -> None:
    if value is None or isinstance(value, str | int | bool):
        return

    if isinstance(value, list):
        for item in value:
            _assert_simple_serializable(item)
        return

    if isinstance(value, dict):
        assert all(isinstance(key, str) for key in value)
        assert "rng_state" not in value
        assert "state" not in value
        for nested_value in value.values():
            _assert_simple_serializable(nested_value)
        return

    raise AssertionError(f"Observation leaked a non-serializable value: {value!r}")


def _assert_no_raw_qm_strings(value: object) -> None:
    if isinstance(value, str):
        assert not value.startswith("qm_")
        return

    if isinstance(value, list):
        for item in value:
            _assert_no_raw_qm_strings(item)
        return

    if isinstance(value, dict):
        for nested_value in value.values():
            _assert_no_raw_qm_strings(nested_value)
