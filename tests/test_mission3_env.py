from __future__ import annotations

from pathlib import Path

import pytest

from solo_wargame_ai.domain.actions import (
    AdvanceAction,
    ChooseOrderExecutionAction,
    DiscardActivationRollAction,
    DoubleChoiceOption,
    GameAction,
    OrderExecutionChoice,
    ResolveDoubleChoiceAction,
    SelectActivationDieAction,
    SelectBritishUnitAction,
    SelectGermanUnitAction,
    TakeCoverAction,
)
from solo_wargame_ai.domain.hexgrid import HexCoord
from solo_wargame_ai.domain.state import TerminalOutcome
from solo_wargame_ai.env.mission3_action_catalog import build_mission3_action_catalog
from solo_wargame_ai.env.mission3_env import (
    IllegalActionIdError,
    InvalidActionIdError,
    Mission3Env,
    default_mission3_terminal_reward,
)
from solo_wargame_ai.io.mission_loader import load_mission

MISSION_PATH = (
    Path(__file__).resolve().parents[1]
    / "configs"
    / "missions"
    / "mission_03_secure_the_building.toml"
)


def _defeat_actions() -> tuple[GameAction, ...]:
    return (
        SelectBritishUnitAction(unit_id="rifle_squad_c"),
        ResolveDoubleChoiceAction(choice=DoubleChoiceOption.REROLL),
        SelectActivationDieAction(die_value=3),
        ChooseOrderExecutionAction(choice=OrderExecutionChoice.BOTH_ORDERS),
        AdvanceAction(destination=HexCoord(0, 3)),
        TakeCoverAction(),
        SelectBritishUnitAction(unit_id="rifle_squad_a"),
        DiscardActivationRollAction(),
        SelectBritishUnitAction(unit_id="rifle_squad_b"),
        DiscardActivationRollAction(),
        SelectBritishUnitAction(unit_id="rifle_squad_c"),
        SelectActivationDieAction(die_value=3),
        ChooseOrderExecutionAction(choice=OrderExecutionChoice.BOTH_ORDERS),
        AdvanceAction(destination=HexCoord(0, 2)),
        TakeCoverAction(),
        SelectBritishUnitAction(unit_id="rifle_squad_a"),
        DiscardActivationRollAction(),
        SelectBritishUnitAction(unit_id="rifle_squad_b"),
        DiscardActivationRollAction(),
        SelectGermanUnitAction(unit_id="qm_1"),
        SelectGermanUnitAction(unit_id="qm_2"),
        SelectGermanUnitAction(unit_id="qm_3"),
        SelectBritishUnitAction(unit_id="rifle_squad_a"),
        DiscardActivationRollAction(),
        SelectBritishUnitAction(unit_id="rifle_squad_b"),
        DiscardActivationRollAction(),
        SelectGermanUnitAction(unit_id="qm_1"),
        SelectGermanUnitAction(unit_id="qm_2"),
        SelectGermanUnitAction(unit_id="qm_3"),
        SelectBritishUnitAction(unit_id="rifle_squad_a"),
        DiscardActivationRollAction(),
        SelectBritishUnitAction(unit_id="rifle_squad_b"),
        DiscardActivationRollAction(),
        SelectGermanUnitAction(unit_id="qm_1"),
        SelectGermanUnitAction(unit_id="qm_2"),
        SelectGermanUnitAction(unit_id="qm_3"),
        SelectBritishUnitAction(unit_id="rifle_squad_a"),
        DiscardActivationRollAction(),
        SelectBritishUnitAction(unit_id="rifle_squad_b"),
        DiscardActivationRollAction(),
        SelectGermanUnitAction(unit_id="qm_1"),
        SelectGermanUnitAction(unit_id="qm_2"),
        SelectGermanUnitAction(unit_id="qm_3"),
        SelectBritishUnitAction(unit_id="rifle_squad_a"),
        DiscardActivationRollAction(),
        SelectBritishUnitAction(unit_id="rifle_squad_b"),
        DiscardActivationRollAction(),
        SelectGermanUnitAction(unit_id="qm_1"),
        SelectGermanUnitAction(unit_id="qm_2"),
        SelectGermanUnitAction(unit_id="qm_3"),
    )


@pytest.fixture
def mission():
    return load_mission(MISSION_PATH)


@pytest.mark.parametrize(
    ("terminal_outcome", "expected_reward"),
    [
        (None, 0.0),
        (TerminalOutcome.VICTORY, 1.0),
        (TerminalOutcome.DEFEAT, -1.0),
    ],
    ids=["nonterminal", "victory", "defeat"],
)
def test_default_mission3_terminal_reward_is_terminal_only(
    terminal_outcome: TerminalOutcome | None,
    expected_reward: float,
) -> None:
    assert default_mission3_terminal_reward(terminal_outcome) == expected_reward


def test_step_requires_reset_before_accepting_action_ids(mission) -> None:
    env = Mission3Env(mission)

    with pytest.raises(
        RuntimeError,
        match=r"Mission3Env\.reset\(\) must be called before step\(\)",
    ):
        env.step(0)


def test_reset_uses_seeded_deterministic_progression_and_initial_legality(mission) -> None:
    env = Mission3Env(mission)
    raw_catalog = build_mission3_action_catalog(mission)
    select_unit_c_id = raw_catalog.encode(
        SelectBritishUnitAction(unit_id="rifle_squad_c"),
    )

    first_reset_observation, first_reset_info = env.reset(seed=0)
    first_step_observation, first_step_reward, first_step_terminated, first_step_truncated, _ = (
        env.step(select_unit_c_id)
    )

    second_reset_observation, second_reset_info = env.reset(seed=0)
    (
        second_step_observation,
        second_step_reward,
        second_step_terminated,
        second_step_truncated,
        _,
    ) = env.step(select_unit_c_id)

    alternate_reset_observation, alternate_reset_info = env.reset(seed=1)
    alternate_step_observation, _, _, _, _ = env.step(select_unit_c_id)

    assert first_reset_observation == second_reset_observation == alternate_reset_observation
    assert first_reset_info == second_reset_info
    assert first_reset_info["seed"] == 0
    assert first_reset_info["action_catalog_size"] == env.action_space_size == 49
    assert first_reset_info["decision_step_count"] == 0
    assert first_reset_info["legal_action_ids"] == [0, 1, 2]
    assert sum(first_reset_info["legal_action_mask"]) == 3

    assert first_step_observation == second_step_observation
    assert first_step_reward == second_step_reward == 0.0
    assert first_step_terminated is second_step_terminated is False
    assert first_step_truncated is second_step_truncated is False
    assert first_step_observation["decision"]["pending_kind"] == "choose_double_choice"
    assert alternate_reset_info["seed"] == 1
    assert alternate_step_observation["decision"]["pending_kind"] == "choose_activation_die"


def test_step_rejects_invalid_action_ids_without_advancing_state(mission) -> None:
    env = Mission3Env(mission)
    raw_catalog = build_mission3_action_catalog(mission)
    _, initial_info = env.reset(seed=0)
    illegal_in_context_action_id = raw_catalog.encode(
        ChooseOrderExecutionAction(choice=OrderExecutionChoice.FIRST_ORDER_ONLY),
    )
    valid_action_id = raw_catalog.encode(
        SelectBritishUnitAction(unit_id="rifle_squad_c"),
    )

    with pytest.raises(
        InvalidActionIdError,
        match="outside the action catalog range for 'mission_03_secure_the_building'",
    ):
        env.step(env.action_space_size)

    with pytest.raises(IllegalActionIdError, match="illegal in the current state"):
        env.step(illegal_in_context_action_id)

    observation, reward, terminated, truncated, info = env.step(valid_action_id)

    assert initial_info["decision_step_count"] == 0
    assert reward == 0.0
    assert terminated is False
    assert truncated is False
    assert info["decision_step_count"] == 1
    assert observation["decision"]["pending_kind"] == "choose_double_choice"


def test_step_runs_full_episode_with_terminal_reward_and_no_default_truncation(mission) -> None:
    env = Mission3Env(mission)
    raw_catalog = build_mission3_action_catalog(mission)
    _, info = env.reset(seed=0)
    encoded_actions = tuple(raw_catalog.encode(action) for action in _defeat_actions())

    for index, action_id in enumerate(encoded_actions, start=1):
        assert action_id in info["legal_action_ids"]
        observation, reward, terminated, truncated, info = env.step(action_id)

        is_final_step = index == len(encoded_actions)
        if is_final_step:
            assert reward == -1.0
            assert terminated is True
            assert truncated is False
            assert observation["terminal_outcome"] == "defeat"
            assert info["terminal_outcome"] == "defeat"
            assert info["decision_step_count"] == len(encoded_actions)
            assert info["legal_action_ids"] == []
            assert info["legal_action_mask"] == [False] * env.action_space_size
        else:
            assert reward == 0.0
            assert terminated is False
            assert truncated is False

    with pytest.raises(RuntimeError, match="episode is closed"):
        env.step(encoded_actions[-1])


def test_step_uses_truncated_only_for_external_step_limit(mission) -> None:
    env = Mission3Env(mission, max_steps=1)
    raw_catalog = build_mission3_action_catalog(mission)
    select_unit_c_id = raw_catalog.encode(
        SelectBritishUnitAction(unit_id="rifle_squad_c"),
    )

    env.reset(seed=0)
    observation, reward, terminated, truncated, info = env.step(select_unit_c_id)

    assert observation["decision"]["pending_kind"] == "choose_double_choice"
    assert reward == 0.0
    assert terminated is False
    assert truncated is True
    assert info["terminal_outcome"] is None
    assert info["truncation_reason"] == "step_limit"
    assert info["legal_action_ids"] == [
        raw_catalog.encode(
            ResolveDoubleChoiceAction(choice=DoubleChoiceOption.KEEP),
        ),
        raw_catalog.encode(
            ResolveDoubleChoiceAction(choice=DoubleChoiceOption.REROLL),
        ),
    ]

    with pytest.raises(RuntimeError, match="episode is closed"):
        env.step(select_unit_c_id)
