from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from solo_wargame_ai.domain.actions import (
    AdvanceAction,
    ChooseOrderExecutionAction,
    DiscardActivationRollAction,
    DoubleChoiceOption,
    FireAction,
    GameAction,
    GrenadeAttackAction,
    OrderExecutionChoice,
    RallyAction,
    ResolveDoubleChoiceAction,
    ScoutAction,
    SelectActivationDieAction,
    SelectBritishUnitAction,
    SelectGermanUnitAction,
    TakeCoverAction,
)
from solo_wargame_ai.domain.enums import HexDirection
from solo_wargame_ai.domain.hexgrid import HexCoord
from solo_wargame_ai.domain.mission import OrderName
from solo_wargame_ai.domain.state import (
    CurrentActivation,
    TerminalOutcome,
    create_initial_game_state,
)
from solo_wargame_ai.domain.units import (
    GermanUnitStatus,
    RevealedGermanUnitState,
    UnresolvedHiddenMarkerState,
)
from solo_wargame_ai.io.mission_loader import load_mission
from solo_wargame_ai.io.replay import (
    ReplayEventKind,
    replay_trace,
    run_action_replay,
    serialize_action,
    summarize_state,
)

MISSION_PATH = (
    Path(__file__).resolve().parents[1]
    / "configs"
    / "missions"
    / "mission_01_secure_the_woods_1.toml"
)


@pytest.mark.parametrize(
    ("action", "expected"),
    [
        (
            SelectBritishUnitAction(unit_id="rifle_squad_a"),
            {"kind": "select_british_unit", "unit_id": "rifle_squad_a"},
        ),
        (
            ResolveDoubleChoiceAction(choice=DoubleChoiceOption.REROLL),
            {"kind": "resolve_double_choice", "choice": "reroll"},
        ),
        (
            SelectActivationDieAction(die_value=5),
            {"kind": "select_activation_die", "die_value": 5},
        ),
        (
            DiscardActivationRollAction(),
            {"kind": "discard_activation_roll"},
        ),
        (
            ChooseOrderExecutionAction(choice=OrderExecutionChoice.BOTH_ORDERS),
            {"kind": "choose_order_execution", "choice": "both_orders"},
        ),
        (
            AdvanceAction(destination=HexCoord(1, 2)),
            {"kind": "advance", "destination": {"q": 1, "r": 2}},
        ),
        (
            FireAction(target_unit_id="qm_1"),
            {"kind": "fire", "target_unit_id": "qm_1"},
        ),
        (
            GrenadeAttackAction(target_unit_id="qm_1"),
            {"kind": "grenade_attack", "target_unit_id": "qm_1"},
        ),
        (
            TakeCoverAction(),
            {"kind": "take_cover"},
        ),
        (
            RallyAction(),
            {"kind": "rally"},
        ),
        (
            ScoutAction(marker_id="qm_1"),
            {"kind": "scout", "marker_id": "qm_1"},
        ),
        (
            ScoutAction(marker_id="qm_1", facing=HexDirection.DOWN_LEFT),
            {"kind": "scout", "marker_id": "qm_1", "facing": "down_left"},
        ),
        (
            SelectGermanUnitAction(unit_id="qm_1"),
            {"kind": "select_german_unit", "unit_id": "qm_1"},
        ),
    ],
)
def test_serialize_action_has_stable_json_friendly_payloads(
    action: GameAction,
    expected: dict[str, object],
) -> None:
    assert serialize_action(action) == expected


def test_summarize_state_sorts_collections_deterministically() -> None:
    mission = load_mission(MISSION_PATH)
    base_state = create_initial_game_state(mission, seed=0)

    state = replace(
        base_state,
        british_units={
            "rifle_squad_b": replace(base_state.british_units["rifle_squad_b"], cover=1),
            "rifle_squad_a": replace(base_state.british_units["rifle_squad_a"], cover=2),
        },
        german_units={
            "qm_b": RevealedGermanUnitState(
                unit_id="qm_b",
                unit_class="rifle_squad",
                position=HexCoord(1, 1),
                facing=HexDirection.DOWN_RIGHT,
                status=GermanUnitStatus.REMOVED,
            ),
            "qm_a": RevealedGermanUnitState(
                unit_id="qm_a",
                unit_class="light_machine_gun",
                position=HexCoord(0, 1),
                facing=HexDirection.DOWN,
                status=GermanUnitStatus.ACTIVE,
            ),
        },
        unresolved_markers={
            "qm_2": UnresolvedHiddenMarkerState(marker_id="qm_2", position=HexCoord(2, 0)),
            "qm_1": UnresolvedHiddenMarkerState(marker_id="qm_1", position=HexCoord(1, 0)),
        },
        activated_british_unit_ids=frozenset({"rifle_squad_b", "rifle_squad_a"}),
        activated_german_unit_ids=frozenset({"qm_b", "qm_a"}),
        current_activation=CurrentActivation(
            active_unit_id="rifle_squad_b",
            roll=(6, 1),
            selected_die=6,
            planned_orders=(OrderName.FIRE, OrderName.ADVANCE),
            next_order_index=1,
        ),
    )

    summary = summarize_state(state)
    summary_dict = summary.to_dict()

    assert summary.activated_british_unit_ids == ("rifle_squad_a", "rifle_squad_b")
    assert summary.activated_german_unit_ids == ("qm_a", "qm_b")
    assert [unit.unit_id for unit in summary.british_units] == ["rifle_squad_a", "rifle_squad_b"]
    assert [unit.unit_id for unit in summary.german_units] == ["qm_a", "qm_b"]
    assert [marker.marker_id for marker in summary.unresolved_markers] == ["qm_1", "qm_2"]
    assert summary_dict["activated_british_unit_ids"] == ["rifle_squad_a", "rifle_squad_b"]
    assert summary_dict["activated_german_unit_ids"] == ["qm_a", "qm_b"]
    assert summary_dict["current_activation"] == {
        "active_unit_id": "rifle_squad_b",
        "roll": [6, 1],
        "selected_die": 6,
        "planned_orders": ["fire", "advance"],
        "next_order_index": 1,
    }
    assert [unit["unit_id"] for unit in summary_dict["british_units"]] == [
        "rifle_squad_a",
        "rifle_squad_b",
    ]
    assert [unit["unit_id"] for unit in summary_dict["german_units"]] == ["qm_a", "qm_b"]
    assert [marker["marker_id"] for marker in summary_dict["unresolved_markers"]] == [
        "qm_1",
        "qm_2",
    ]


def test_replay_trace_to_dict_is_json_serializable_and_preserves_structured_events() -> None:
    mission = load_mission(MISSION_PATH)
    run = run_action_replay(mission, seed=0, actions=_victory_actions())

    payload = run.trace.to_dict()
    reveal_event = next(
        event
        for step in payload["steps"]
        for event in step["events"]
        if event["kind"] == ReplayEventKind.REVEAL_RESOLVED.value
    )
    attack_event = next(
        event
        for step in payload["steps"]
        for event in step["events"]
        if event["kind"] == ReplayEventKind.ATTACK_RESOLVED.value
    )
    terminal_event = next(
        event
        for step in payload["steps"]
        for event in step["events"]
        if event["kind"] == ReplayEventKind.TERMINAL_OUTCOME_SET.value
    )

    assert payload == run.trace.to_dict()
    assert payload["mission_id"] == mission.mission_id
    assert payload["initial_seed"] == 0
    assert payload["steps"][0]["action"] == {
        "kind": "select_british_unit",
        "unit_id": "rifle_squad_a",
    }
    assert payload["steps"][0]["after"]["current_activation"] == {
        "active_unit_id": "rifle_squad_a",
        "roll": [4, 4],
        "selected_die": None,
        "planned_orders": [],
        "next_order_index": 0,
    }
    assert reveal_event["details"] == {
        "marker_id": "qm_1",
        "method": "movement",
        "roll": 5,
        "unit_class": "light_machine_gun",
        "position": {"q": 0, "r": 1},
        "facing": "down",
    }
    assert attack_event["details"] == {
        "side": "german",
        "attack_kind": "german_fire",
        "attacker_unit_id": "qm_1",
        "target_unit_id": "rifle_squad_b",
        "threshold": 6,
        "roll": [2, 3],
        "roll_total": 5,
        "hit": False,
    }
    assert terminal_event["details"] == {"outcome": "victory"}
    assert payload["final_state"]["terminal_outcome"] == "victory"
    assert json.loads(json.dumps(payload)) == payload


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


def _morale_loss_actions() -> tuple[GameAction, ...]:
    return _victory_actions()[:16]


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


@pytest.mark.parametrize(
    (
        "seed",
        "actions",
        "expected_terminal",
        "expected_phase",
        "expected_pending",
        "required_events",
    ),
    [
        (
            0,
            _victory_actions(),
            TerminalOutcome.VICTORY,
            "british",
            "choose_british_unit",
            {
                ReplayEventKind.REVEAL_RESOLVED,
                ReplayEventKind.ATTACK_RESOLVED,
                ReplayEventKind.UNIT_REMOVED,
                ReplayEventKind.TERMINAL_OUTCOME_SET,
            },
        ),
        (
            2,
            _morale_loss_actions(),
            None,
            "british",
            "choose_british_unit",
            {
                ReplayEventKind.REVEAL_RESOLVED,
                ReplayEventKind.ATTACK_RESOLVED,
                ReplayEventKind.MORALE_CHANGED,
            },
        ),
        (
            3,
            _defeat_actions(),
            TerminalOutcome.DEFEAT,
            "german",
            "choose_german_unit",
            {
                ReplayEventKind.TURN_ADVANCED,
                ReplayEventKind.TERMINAL_OUTCOME_SET,
            },
        ),
    ],
    ids=["victory", "morale_loss", "defeat"],
)
def test_replay_round_trip_matrix_covers_representative_seeded_trajectories(
    seed: int,
    actions: tuple[GameAction, ...],
    expected_terminal: TerminalOutcome | None,
    expected_phase: str,
    expected_pending: str,
    required_events: set[ReplayEventKind],
) -> None:
    mission = load_mission(MISSION_PATH)

    run = run_action_replay(mission, seed=seed, actions=actions)
    replayed = replay_trace(mission, run.trace)
    event_kinds = {event.kind for step in run.trace.steps for event in step.events}

    assert replayed.trace == run.trace
    assert replayed.trace.to_dict() == run.trace.to_dict()
    assert replayed.final_state == run.final_state
    assert run.final_state.terminal_outcome is expected_terminal
    assert run.trace.final_state.terminal_outcome == (
        None if expected_terminal is None else expected_terminal.value
    )
    assert run.trace.final_state.phase == expected_phase
    assert run.trace.final_state.pending_decision == expected_pending
    assert required_events <= event_kinds
