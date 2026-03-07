from __future__ import annotations

from pathlib import Path

from solo_wargame_ai.domain.actions import (
    AdvanceAction,
    ChooseOrderExecutionAction,
    DiscardActivationRollAction,
    DoubleChoiceOption,
    FireAction,
    OrderExecutionChoice,
    ResolveDoubleChoiceAction,
    SelectActivationDieAction,
    SelectBritishUnitAction,
    SelectGermanUnitAction,
)
from solo_wargame_ai.domain.hexgrid import HexCoord
from solo_wargame_ai.domain.state import TerminalOutcome
from solo_wargame_ai.io.mission_loader import load_mission
from solo_wargame_ai.io.replay import (
    ReplayEventKind,
    render_replay_trace,
    replay_trace,
    run_action_replay,
    summarize_state,
)

MISSION_PATH = (
    Path(__file__).resolve().parents[1]
    / "configs"
    / "missions"
    / "mission_01_secure_the_woods_1.toml"
)


def test_same_seed_and_actions_produce_identical_trace_and_final_state_summary() -> None:
    mission = load_mission(MISSION_PATH)
    actions = _victory_actions()

    first_run = run_action_replay(mission, seed=0, actions=actions)
    second_run = run_action_replay(mission, seed=0, actions=actions)
    replayed = replay_trace(mission, first_run.trace)

    assert first_run.trace == second_run.trace
    assert first_run.trace.final_state == second_run.trace.final_state
    assert first_run.trace.final_state == summarize_state(first_run.final_state)
    assert replayed.trace == first_run.trace
    assert replayed.final_state.terminal_outcome is TerminalOutcome.VICTORY


def test_trace_contains_meaningful_structured_records_and_deterministic_text() -> None:
    mission = load_mission(MISSION_PATH)
    run = run_action_replay(mission, seed=0, actions=_victory_actions())

    assert run.trace.steps

    event_kinds = {
        event.kind
        for step in run.trace.steps
        for event in step.events
    }
    assert ReplayEventKind.ACTION_SELECTED in event_kinds
    assert ReplayEventKind.RANDOM_DRAW in event_kinds
    assert ReplayEventKind.REVEAL_RESOLVED in event_kinds
    assert ReplayEventKind.ATTACK_RESOLVED in event_kinds
    assert ReplayEventKind.UNIT_REMOVED in event_kinds
    assert ReplayEventKind.PHASE_ADVANCED in event_kinds
    assert ReplayEventKind.TURN_ADVANCED in event_kinds
    assert ReplayEventKind.TERMINAL_OUTCOME_SET in event_kinds

    rendered_once = render_replay_trace(run.trace)
    rendered_twice = render_replay_trace(run.trace)

    assert rendered_once
    assert rendered_once == rendered_twice
    assert "Mission mission_01_secure_the_woods_1 seed=0 steps=22" in rendered_once
    assert "reveal marker=qm_1" in rendered_once
    assert "terminal outcome=victory" in rendered_once


def test_trace_records_morale_change_when_german_fire_hits() -> None:
    mission = load_mission(MISSION_PATH)
    run = run_action_replay(mission, seed=2, actions=_reveal_then_german_fire_actions())

    morale_events = [
        event
        for step in run.trace.steps
        for event in step.events
        if event.kind is ReplayEventKind.MORALE_CHANGED
    ]

    assert len(morale_events) == 1
    assert morale_events[0].details == {
        "unit_id": "rifle_squad_b",
        "from_morale": "normal",
        "to_morale": "low",
        "cause": "german_fire",
    }


def test_fixed_seed_victory_trace_regression_text() -> None:
    mission = load_mission(MISSION_PATH)
    run = run_action_replay(mission, seed=0, actions=_victory_actions())

    assert render_replay_trace(run.trace) == EXPECTED_VICTORY_TRACE_TEXT


EXPECTED_VICTORY_TRACE_TEXT = "\n".join(
    [
        "Mission mission_01_secure_the_woods_1 seed=0 steps=22",
        "Start turn=1 phase=british pending=choose_british_unit",
        "01 T1 british select_british_unit(unit_id=rifle_squad_a)",
        "   random activation_roll [4, 4] unit_id=rifle_squad_a",
        "02 T1 british resolve_double_choice(choice=keep)",
        "03 T1 british discard_activation_roll()",
        "04 T1 british select_british_unit(unit_id=rifle_squad_b)",
        "   random activation_roll [1, 3] unit_id=rifle_squad_b",
        "05 T1 british discard_activation_roll()",
        "   turn 1 -> 2",
        "06 T2 british select_british_unit(unit_id=rifle_squad_a)",
        "   random activation_roll [5, 4] unit_id=rifle_squad_a",
        "07 T2 british discard_activation_roll()",
        "08 T2 british select_british_unit(unit_id=rifle_squad_b)",
        "   random activation_roll [4, 3] unit_id=rifle_squad_b",
        "09 T2 british discard_activation_roll()",
        "   turn 2 -> 3",
        "10 T3 british select_british_unit(unit_id=rifle_squad_a)",
        "   random activation_roll [4, 3] unit_id=rifle_squad_a",
        "11 T3 british discard_activation_roll()",
        "12 T3 british select_british_unit(unit_id=rifle_squad_b)",
        "   random activation_roll [5, 2] unit_id=rifle_squad_b",
        "13 T3 british select_activation_die(die_value=2)",
        "14 T3 british choose_order_execution(choice=first_order_only)",
        "15 T3 british advance(destination=(0, 2))",
        "   random reveal_table [5] marker_id=qm_1 method=movement",
        (
            "   reveal marker=qm_1 method=movement roll=5 "
            "unit_class=light_machine_gun facing=down position=(0, 1)"
        ),
        "   phase british -> german",
        "16 T3 german select_german_unit(unit_id=qm_1)",
        "   random german_fire [2, 3] attacker_unit_id=qm_1 target_unit_id=rifle_squad_b",
        "   attack german_fire qm_1 -> rifle_squad_b roll=5 threshold=6 hit=False",
        "   phase german -> british",
        "   turn 3 -> 4",
        "17 T4 british select_british_unit(unit_id=rifle_squad_a)",
        "   random activation_roll [2, 1] unit_id=rifle_squad_a",
        "18 T4 british discard_activation_roll()",
        "19 T4 british select_british_unit(unit_id=rifle_squad_b)",
        "   random activation_roll [5, 3] unit_id=rifle_squad_b",
        "20 T4 british select_activation_die(die_value=5)",
        "21 T4 british choose_order_execution(choice=both_orders)",
        "22 T4 british fire(target_unit_id=qm_1)",
        (
            "   random british_attack [5, 6] attack_kind=fire "
            "attacker_unit_id=rifle_squad_b target_unit_id=qm_1"
        ),
        "   attack fire rifle_squad_b -> qm_1 roll=11 threshold=9 hit=True",
        "   removed side=german unit_id=qm_1 cause=fire",
        "   terminal outcome=victory",
        "End turn=4 phase=british pending=choose_british_unit terminal=victory",
    ],
)


def _victory_actions() -> tuple[object, ...]:
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


def _reveal_then_german_fire_actions() -> tuple[object, ...]:
    return _victory_actions()[:16]
