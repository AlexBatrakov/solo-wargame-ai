from __future__ import annotations

from pathlib import Path

import pytest

from solo_wargame_ai.agents.rollout_search_agent import (
    RolloutEvaluation,
    RolloutSearchAgent,
)
from solo_wargame_ai.domain.resolver import get_legal_actions
from solo_wargame_ai.domain.state import TerminalOutcome, create_initial_game_state
from solo_wargame_ai.io.mission_loader import load_mission

MISSION_PATH = (
    Path(__file__).resolve().parents[2]
    / "configs"
    / "missions"
    / "mission_01_secure_the_woods_1.toml"
)


def test_rollout_search_agent_selects_only_from_the_provided_legal_actions() -> None:
    mission = load_mission(MISSION_PATH)
    state = create_initial_game_state(mission, seed=0)
    legal_actions = get_legal_actions(state)
    agent_a = RolloutSearchAgent()
    agent_b = RolloutSearchAgent()

    first_choice = agent_a.select_action(state, legal_actions)
    second_choice = agent_b.select_action(state, legal_actions)

    assert first_choice == second_choice
    assert first_choice in legal_actions


def test_rollout_search_agent_rejects_empty_legal_action_sets() -> None:
    mission = load_mission(MISSION_PATH)
    state = create_initial_game_state(mission, seed=0)

    with pytest.raises(ValueError, match="at least one legal action"):
        RolloutSearchAgent().select_action(state, ())


def test_rollout_search_agent_evaluates_each_root_action_once_in_legal_order(
    monkeypatch,
) -> None:
    mission = load_mission(MISSION_PATH)
    state = create_initial_game_state(mission, seed=0)
    legal_actions = get_legal_actions(state)
    agent = RolloutSearchAgent()
    evaluated_actions: list[object] = []

    def fake_evaluate_action_rollout(*, state, action):  # type: ignore[no-untyped-def]
        del state
        evaluated_actions.append(action)
        return RolloutEvaluation(
            terminal_outcome=TerminalOutcome.DEFEAT,
            terminal_turn=4,
            resolved_marker_count=0,
            removed_german_count=0,
            player_decision_count=10,
        )

    monkeypatch.setattr(
        agent,
        "_evaluate_action_rollout",
        lambda state, action: fake_evaluate_action_rollout(state=state, action=action),
    )

    selected_action = agent.select_action(state, legal_actions)

    assert evaluated_actions == list(legal_actions)
    assert selected_action == legal_actions[0]


def test_rollout_search_agent_prefers_terminal_victory_over_secondary_tiebreaks(
    monkeypatch,
) -> None:
    mission = load_mission(MISSION_PATH)
    state = create_initial_game_state(mission, seed=0)
    legal_actions = get_legal_actions(state)
    agent = RolloutSearchAgent()

    losing_action, winning_action = legal_actions

    def fake_evaluate_action_rollout(*, action):  # type: ignore[no-untyped-def]
        if action == losing_action:
            return RolloutEvaluation(
                terminal_outcome=TerminalOutcome.DEFEAT,
                terminal_turn=2,
                resolved_marker_count=1,
                removed_german_count=1,
                player_decision_count=3,
            )
        if action == winning_action:
            return RolloutEvaluation(
                terminal_outcome=TerminalOutcome.VICTORY,
                terminal_turn=5,
                resolved_marker_count=0,
                removed_german_count=0,
                player_decision_count=12,
            )
        raise AssertionError(f"Unexpected action: {action!r}")

    monkeypatch.setattr(
        agent,
        "_evaluate_action_rollout",
        lambda state, action: fake_evaluate_action_rollout(action=action),
    )

    assert agent.select_action(state, legal_actions) == winning_action
