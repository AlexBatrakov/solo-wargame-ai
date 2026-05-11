from __future__ import annotations

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
from solo_wargame_ai.interactive.session import PlaySession
from solo_wargame_ai.io.replay import serialize_action


def test_event_log_explains_activation_rolls_reveals_attacks_and_terminal(mission) -> None:
    session = PlaySession(mission, default_seed=0)

    view = _play_actions(session, _victory_actions())

    messages = [event["message"] for event in view["event_log"]]
    assert messages[:2] == [
        "Action: Activate Rifle Squad A.",
        "Rifle Squad A rolled 4, 4 for activation.",
    ]
    assert "Movement reveal ?1: roll 5 -> Light machine gun facing Down." in messages
    assert "LMG 1 fires at Rifle Squad B: roll 5 vs 6 -> miss." in messages
    assert "Rifle Squad B fires at LMG 1: roll 11 vs 9 -> hit." in messages
    assert "Removed: LMG 1." in messages
    assert messages[-1] == "Outcome: Victory."
    assert view["last_action_events"] == [
        {
            "id": "22:1",
            "step": 22,
            "kind": "action_selected",
            "message": "Action: Fire at LMG 1.",
        },
        {
            "id": "22:2",
            "step": 22,
            "kind": "attack_resolved",
            "message": "Rifle Squad B fires at LMG 1: roll 11 vs 9 -> hit.",
        },
        {
            "id": "22:3",
            "step": 22,
            "kind": "unit_removed",
            "message": "Removed: LMG 1.",
        },
        {
            "id": "22:4",
            "step": 22,
            "kind": "terminal_outcome_set",
            "message": "Outcome: Victory.",
        },
    ]


def test_event_log_explains_german_fire_morale_change(mission) -> None:
    session = PlaySession(mission, default_seed=2)

    view = _play_actions(session, _reveal_then_german_fire_actions())

    assert [event["message"] for event in view["last_action_events"]] == [
        "Action: Resolve German fire: HMG 1.",
        "HMG 1 fires at Rifle Squad B: roll 11 vs 5 -> hit.",
        "Morale: Rifle Squad B Normal -> Low.",
        "Phase: German -> British.",
        "Turn: 3 -> 4.",
    ]


def test_event_log_resets_with_session(mission) -> None:
    session = PlaySession(mission, default_seed=0)
    view = session.current_view()

    session.apply_ui_action(
        _action_id_for(view, SelectBritishUnitAction(unit_id="rifle_squad_a")),
    )
    reset_view = session.reset(seed=0)

    assert reset_view["event_log"] == []
    assert reset_view["last_action_events"] == []


def _play_actions(session: PlaySession, actions: tuple[GameAction, ...]) -> dict[str, object]:
    view = session.current_view()
    for action in actions:
        view = session.apply_ui_action(_action_id_for(view, action))
    return view


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


def _reveal_then_german_fire_actions() -> tuple[GameAction, ...]:
    return _victory_actions()[:16]
