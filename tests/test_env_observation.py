from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from solo_wargame_ai.domain.decision_context import ChooseGermanUnitContext
from solo_wargame_ai.domain.state import GamePhase, create_initial_game_state
from solo_wargame_ai.env import (
    build_legal_action_selection,
    build_mission1_action_catalog,
    build_observation,
    normalize_env_state,
)
from solo_wargame_ai.io.mission_loader import load_mission

MISSION_PATH = (
    Path(__file__).resolve().parents[1]
    / "configs"
    / "missions"
    / "mission_01_secure_the_woods_1.toml"
)


def test_observation_and_legality_share_the_same_normalized_state_boundary() -> None:
    mission = load_mission(MISSION_PATH)
    catalog = build_mission1_action_catalog(mission)
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
    observation = build_observation(normalized_state)
    legal_selection = build_legal_action_selection(normalized_state, catalog)

    assert raw_state.phase is GamePhase.GERMAN
    assert normalized_state.state.phase is GamePhase.BRITISH
    assert normalized_state.state.turn == 2
    assert observation["phase"] == "british"
    assert observation["turn"] == 2
    assert observation["decision"]["pending_kind"] == "choose_british_unit"
    assert legal_selection.legal_action_ids == (0, 1)


def test_observation_contains_only_simple_serializable_values_and_visible_marker_positions(
) -> None:
    mission = load_mission(MISSION_PATH)
    normalized_state = normalize_env_state(create_initial_game_state(mission, seed=0))

    observation = build_observation(normalized_state)

    assert observation["unresolved_markers"] == [
        {
            "marker_id": "qm_1",
            "position": {"q": 0, "r": 1},
        },
    ]
    _assert_simple_serializable(observation)


def _assert_simple_serializable(value: object) -> None:
    if value is None or isinstance(value, str | int | bool):
        return

    if isinstance(value, list):
        for item in value:
            _assert_simple_serializable(item)
        return

    if isinstance(value, dict):
        assert all(isinstance(key, str) for key in value)
        for nested_value in value.values():
            _assert_simple_serializable(nested_value)
        return

    raise AssertionError(f"Observation leaked a non-serializable value: {value!r}")
