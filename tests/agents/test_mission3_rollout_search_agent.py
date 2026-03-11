from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from solo_wargame_ai.agents.mission3_rollout_search_agent import (
    DEFAULT_MISSION3_SEARCH_BUDGET,
    Mission3RolloutEvaluation,
    Mission3RolloutSearchAgent,
)
from solo_wargame_ai.domain.actions import AdvanceAction
from solo_wargame_ai.domain.decision_context import ChooseOrderParameterContext
from solo_wargame_ai.domain.hexgrid import HexCoord
from solo_wargame_ai.domain.mission import OrderName
from solo_wargame_ai.domain.resolver import apply_action, get_legal_actions
from solo_wargame_ai.domain.state import (
    CurrentActivation,
    create_initial_game_state,
    validate_game_state,
)
from solo_wargame_ai.io.mission_loader import load_mission

MISSION_PATH = (
    Path(__file__).resolve().parents[2]
    / "configs"
    / "missions"
    / "mission_03_secure_the_building.toml"
)


@pytest.mark.parametrize(
    "agent_factory",
    [
        Mission3RolloutSearchAgent,
    ],
)
def test_mission3_rollout_search_selects_only_from_the_provided_legal_actions(
    agent_factory,
) -> None:
    mission = load_mission(MISSION_PATH)
    state = create_initial_game_state(mission, seed=0)
    legal_actions = get_legal_actions(state)
    agent_a = agent_factory()
    agent_b = agent_factory()

    first_choice = agent_a.select_action(state, legal_actions)
    second_choice = agent_b.select_action(state, legal_actions)

    assert first_choice == second_choice
    assert first_choice in legal_actions


def test_mission3_rollout_search_budget_is_explicit_and_fixed() -> None:
    assert DEFAULT_MISSION3_SEARCH_BUDGET.root_width_policy == "full_legal_width"
    assert DEFAULT_MISSION3_SEARCH_BUDGET.rollouts_per_action == 1
    assert DEFAULT_MISSION3_SEARCH_BUDGET.rollout_depth_limit == 16


def test_mission3_rollout_search_evaluates_each_root_action_once_in_legal_order(
    monkeypatch,
) -> None:
    mission = load_mission(MISSION_PATH)
    base_state = create_initial_game_state(mission, seed=0)
    state = replace(
        base_state,
        british_units={
            **base_state.british_units,
            "rifle_squad_a": replace(
                base_state.british_units["rifle_squad_a"],
                position=HexCoord(0, 3),
            ),
        },
        pending_decision=ChooseOrderParameterContext(
            order=OrderName.ADVANCE,
            order_index=0,
        ),
        current_activation=CurrentActivation(
            active_unit_id="rifle_squad_a",
            roll=(6, 2),
            selected_die=2,
            planned_orders=(OrderName.ADVANCE,),
            next_order_index=0,
        ),
    )
    validate_game_state(state)

    legal_actions = get_legal_actions(state)
    reveal_action = AdvanceAction(destination=HexCoord(0, 2))
    agent = Mission3RolloutSearchAgent()
    evaluated_actions: list[object] = []

    def fake_evaluate_action_rollout(*, action):  # type: ignore[no-untyped-def]
        evaluated_actions.append(action)
        return Mission3RolloutEvaluation(
            terminal_outcome=None,
            terminal_turn=state.turn,
            resolved_marker_count=3 if action == reveal_action else 0,
            removed_german_count=0,
            player_decision_count=agent.budget.rollout_depth_limit,
            frontier_score=50.0 if action == reveal_action else 0.0,
            truncated=True,
        )

    monkeypatch.setattr(
        agent,
        "_evaluate_action_rollout",
        lambda state, action: fake_evaluate_action_rollout(action=action),
    )

    selected_action = agent.select_action(state, legal_actions)

    assert evaluated_actions == list(legal_actions)
    assert selected_action == reveal_action


def test_mission3_rollout_search_preserves_legality_across_short_seeded_runs() -> None:
    mission = load_mission(MISSION_PATH)

    for seed in (0, 1, 2):
        state = create_initial_game_state(mission, seed=seed)
        agent = Mission3RolloutSearchAgent()
        decision_count = 0
        while state.terminal_outcome is None and decision_count < 8:
            legal_actions = get_legal_actions(state)
            assert legal_actions
            action = agent.select_action(state, legal_actions)
            assert action in legal_actions
            state = apply_action(state, action)
            decision_count += 1
