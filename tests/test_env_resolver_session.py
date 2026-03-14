from __future__ import annotations

from pathlib import Path

import pytest

from solo_wargame_ai.domain.actions import (
    AdvanceAction,
    ChooseOrderExecutionAction,
    DiscardActivationRollAction,
    DoubleChoiceOption,
    FireAction,
    GameAction,
    OrderExecutionChoice,
    ResolveDoubleChoiceAction,
    SelectActivationDieAction,
    SelectBritishUnitAction,
    SelectGermanUnitAction,
)
from solo_wargame_ai.domain.hexgrid import HexCoord
from solo_wargame_ai.domain.state import create_initial_game_state
from solo_wargame_ai.env.normalized_state import normalize_env_state
from solo_wargame_ai.env.resolver_session import ResolverEnvSession
from solo_wargame_ai.io.mission_loader import load_mission

MISSION_PATH = (
    Path(__file__).resolve().parents[1]
    / "configs"
    / "missions"
    / "mission_01_secure_the_woods_1.toml"
)


def _victory_actions() -> tuple[GameAction, ...]:
    return (
        SelectBritishUnitAction(unit_id="rifle_squad_a"),
        ResolveDoubleChoiceAction(choice=DoubleChoiceOption.KEEP),
        DiscardActivationRollAction(),
        SelectBritishUnitAction(unit_id="rifle_squad_b"),
        DiscardActivationRollAction(),
        SelectBritishUnitAction(unit_id="rifle_squad_a"),
        DiscardActivationRollAction(),
        SelectBritishUnitAction(unit_id="rifle_squad_b"),
        DiscardActivationRollAction(),
        SelectBritishUnitAction(unit_id="rifle_squad_a"),
        DiscardActivationRollAction(),
        SelectBritishUnitAction(unit_id="rifle_squad_b"),
        SelectActivationDieAction(die_value=2),
        ChooseOrderExecutionAction(choice=OrderExecutionChoice.FIRST_ORDER_ONLY),
        AdvanceAction(destination=HexCoord(0, 2)),
        SelectGermanUnitAction(unit_id="qm_1"),
        SelectBritishUnitAction(unit_id="rifle_squad_a"),
        DiscardActivationRollAction(),
        SelectBritishUnitAction(unit_id="rifle_squad_b"),
        SelectActivationDieAction(die_value=5),
        ChooseOrderExecutionAction(choice=OrderExecutionChoice.BOTH_ORDERS),
        FireAction(target_unit_id="qm_1"),
    )


@pytest.fixture
def mission():
    return load_mission(MISSION_PATH)


def test_reset_builds_the_same_normalized_state_boundary_as_the_existing_helper(mission) -> None:
    session = ResolverEnvSession(mission)

    snapshot = session.reset(seed=0)
    expected = normalize_env_state(create_initial_game_state(mission, seed=0))

    assert snapshot.seed == 0
    assert snapshot.decision_step_count == 0
    assert snapshot.terminated is False
    assert snapshot.truncated is False
    assert snapshot.episode_closed is False
    assert snapshot.truncation_reason is None
    assert snapshot.normalized_state == expected
    assert snapshot.normalized_state.legal_actions == (
        SelectBritishUnitAction(unit_id="rifle_squad_a"),
        SelectBritishUnitAction(unit_id="rifle_squad_b"),
    )


def test_step_limit_truncates_after_applying_one_raw_legal_action(mission) -> None:
    session = ResolverEnvSession(mission, max_steps=1)
    initial_snapshot = session.reset(seed=0)

    next_snapshot = session.step(initial_snapshot.normalized_state.legal_actions[0])

    assert next_snapshot.seed == 0
    assert next_snapshot.decision_step_count == 1
    assert next_snapshot.terminated is False
    assert next_snapshot.truncated is True
    assert next_snapshot.episode_closed is True
    assert next_snapshot.truncation_reason == "step_limit"
    assert (
        next_snapshot.normalized_state.state.pending_decision.kind.value
        == "choose_double_choice"
    )
    assert next_snapshot.normalized_state.legal_actions == (
        ResolveDoubleChoiceAction(choice=DoubleChoiceOption.KEEP),
        ResolveDoubleChoiceAction(choice=DoubleChoiceOption.REROLL),
    )


def test_terminal_session_closes_with_empty_raw_legal_actions(mission) -> None:
    session = ResolverEnvSession(mission)
    snapshot = session.reset(seed=0)

    for action in _victory_actions():
        assert action in snapshot.normalized_state.legal_actions
        snapshot = session.step(action)

    assert snapshot.decision_step_count == len(_victory_actions())
    assert snapshot.terminated is True
    assert snapshot.truncated is False
    assert snapshot.episode_closed is True
    assert snapshot.truncation_reason is None
    assert snapshot.normalized_state.state.terminal_outcome.value == "victory"
    assert snapshot.normalized_state.legal_actions == ()

    with pytest.raises(RuntimeError, match="ResolverEnvSession episode is closed"):
        session.step(_victory_actions()[-1])
