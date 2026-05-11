from __future__ import annotations

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
from solo_wargame_ai.interactive.session import (
    InvalidUIActionIdError,
    PlaySession,
    StaleUIActionIdError,
    TerminalSessionError,
)
from solo_wargame_ai.io.replay import serialize_action


def test_session_reset_and_apply_legal_ui_action_updates_state(mission) -> None:
    session = PlaySession(mission, default_seed=0)
    initial_view = session.current_view()
    action_id = initial_view["legal_actions"][0]["id"]

    next_view = session.apply_ui_action(action_id)

    assert next_view["session"]["seed"] == 0
    assert next_view["session"]["decision_step_count"] == 1
    assert next_view["pending_decision"]["kind"] == "choose_double_choice"
    assert next_view["current_activation"]["active_unit_id"] == "rifle_squad_a"
    assert [action["label"] for action in next_view["legal_actions"]] == [
        "Keep double 4: Fire + Take cover",
        "Reroll the double",
    ]


def test_stale_and_invalid_ui_action_ids_fail_cleanly(mission) -> None:
    session = PlaySession(mission, default_seed=0)
    initial_view = session.current_view()
    stale_action_id = initial_view["legal_actions"][0]["id"]

    session.apply_ui_action(stale_action_id)

    with pytest.raises(StaleUIActionIdError) as stale_error:
        session.apply_ui_action(stale_action_id)
    assert stale_error.value.code == "stale_action_id"
    assert stale_error.value.status_code == 409
    assert stale_error.value.to_payload()["error"]["code"] == "stale_action_id"

    with pytest.raises(InvalidUIActionIdError) as invalid_error:
        session.apply_ui_action("not-an-action-id")
    assert invalid_error.value.code == "invalid_action_id"
    assert invalid_error.value.status_code == 400


def test_reset_rebuilds_the_initial_frontier_for_a_seed(mission) -> None:
    session = PlaySession(mission, default_seed=0)
    initial_view = session.current_view()

    session.apply_ui_action(initial_view["legal_actions"][0]["id"])
    reset_view = session.reset(seed=0)

    assert reset_view["session"]["seed"] == 0
    assert reset_view["session"]["decision_step_count"] == 0
    assert reset_view["state_token"] == initial_view["state_token"]
    assert [action["id"] for action in reset_view["legal_actions"]] == [
        action["id"] for action in initial_view["legal_actions"]
    ]

    other_seed_view = session.reset(seed=7)
    assert other_seed_view["state_token"] != initial_view["state_token"]


def test_mission_1_seed_0_can_reach_terminal_victory_through_ui_ids(mission) -> None:
    session = PlaySession(mission, default_seed=0)
    actions = _victory_actions()

    view = session.current_view()
    for expected_action in actions:
        view = session.apply_ui_action(_action_id_for(view, expected_action))

    assert view["session"]["decision_step_count"] == len(actions)
    assert view["session"]["closed"] is True
    assert view["terminal_outcome"] == "victory"
    assert view["legal_actions"] == []

    with pytest.raises(TerminalSessionError):
        session.apply_ui_action("anything")


def test_mission_1_turn_limit_defeat_is_visible_immediately_after_resolver_terminal(
    mission,
) -> None:
    session = PlaySession(mission, default_seed=3)

    view = session.current_view()
    for expected_action in _defeat_actions():
        view = session.apply_ui_action(_action_id_for(view, expected_action))

    assert view["session"]["closed"] is True
    assert view["terminal_outcome"] == "defeat"
    assert view["legal_actions"] == []


def _action_id_for(view: dict[str, object], action: GameAction) -> str:
    payload = serialize_action(action)
    for action_view in view["legal_actions"]:
        if action_view["payload"] == payload:
            return action_view["id"]
    raise AssertionError(f"Missing UI action for {payload!r}")


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


def _defeat_actions() -> tuple[GameAction, ...]:
    return (
        SelectBritishUnitAction(unit_id="rifle_squad_a"),
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
        DiscardActivationRollAction(),
        SelectBritishUnitAction(unit_id="rifle_squad_a"),
        DiscardActivationRollAction(),
        SelectBritishUnitAction(unit_id="rifle_squad_b"),
        DiscardActivationRollAction(),
    )
