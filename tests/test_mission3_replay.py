from __future__ import annotations

from pathlib import Path

from solo_wargame_ai.domain.actions import (
    AdvanceAction,
    ChooseOrderExecutionAction,
    DiscardActivationRollAction,
    DoubleChoiceOption,
    OrderExecutionChoice,
    ResolveDoubleChoiceAction,
    SelectActivationDieAction,
    SelectBritishUnitAction,
    SelectGermanUnitAction,
    TakeCoverAction,
)
from solo_wargame_ai.domain.hexgrid import HexCoord
from solo_wargame_ai.domain.state import GamePhase
from solo_wargame_ai.io.mission_loader import load_mission
from solo_wargame_ai.io.replay import (
    ReplayEventKind,
    render_replay_trace,
    replay_trace,
    run_action_replay,
    summarize_state,
)

MISSION_03_PATH = (
    Path(__file__).resolve().parents[1]
    / "configs"
    / "missions"
    / "mission_03_secure_the_building.toml"
)


def test_mission_3_replay_trace_is_stable_and_replayable() -> None:
    mission = load_mission(MISSION_03_PATH)
    actions = _mission_3_reveal_trace_actions()

    run = run_action_replay(mission, seed=0, actions=actions)
    replayed = replay_trace(mission, run.trace)

    reveal_events = [
        event
        for step in run.trace.steps
        for event in step.events
        if event.kind is ReplayEventKind.REVEAL_RESOLVED
    ]
    attack_events = [
        event
        for step in run.trace.steps
        for event in step.events
        if event.kind is ReplayEventKind.ATTACK_RESOLVED
    ]
    morale_events = [
        event
        for step in run.trace.steps
        for event in step.events
        if event.kind is ReplayEventKind.MORALE_CHANGED
    ]
    removed_events = [
        event
        for step in run.trace.steps
        for event in step.events
        if event.kind is ReplayEventKind.UNIT_REMOVED
    ]

    assert replayed.trace == run.trace
    assert replayed.final_state == run.final_state
    assert run.trace.final_state == summarize_state(run.final_state)
    assert run.final_state.turn == 3
    assert run.final_state.phase is GamePhase.BRITISH
    assert run.final_state.british_units["rifle_squad_c"].morale.value == "removed"
    assert len(reveal_events) == 3
    assert [event.details["unit_class"] for event in reveal_events] == [
        "german_rifle_squad",
        "heavy_machine_gun",
        "german_rifle_squad",
    ]
    assert [event.details["marker_id"] for event in reveal_events] == ["qm_1", "qm_2", "qm_3"]
    assert [event.details["threshold"] for event in attack_events] == [8, 6]
    assert [event.details["attacker_unit_id"] for event in attack_events] == ["qm_1", "qm_2"]
    assert [event.details["to_morale"] for event in morale_events] == ["low", "removed"]
    assert removed_events[0].details == {
        "side": "british",
        "unit_id": "rifle_squad_c",
        "cause": "german_fire",
    }

    rendered = render_replay_trace(run.trace)
    assert "Mission mission_03_secure_the_building seed=0 steps=22" in rendered
    assert "reveal marker=qm_1 method=movement roll=5 unit_class=german_rifle_squad" in rendered
    assert "removed side=british unit_id=rifle_squad_c cause=german_fire" in rendered


def _mission_3_reveal_trace_actions() -> tuple[object, ...]:
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
    )
