from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from solo_wargame_ai.domain.actions import (
    AdvanceAction,
    ChooseOrderExecutionAction,
    DiscardActivationRollAction,
    DoubleChoiceOption,
    FireAction,
    GrenadeAttackAction,
    OrderExecutionChoice,
    ResolveDoubleChoiceAction,
    ScoutAction,
    SelectActivationDieAction,
    SelectBritishUnitAction,
    SelectGermanUnitAction,
)
from solo_wargame_ai.domain.decision_context import (
    ChooseActivationDieContext,
    ChooseOrderExecutionContext,
)
from solo_wargame_ai.domain.enums import HexDirection
from solo_wargame_ai.domain.hexgrid import HexCoord
from solo_wargame_ai.domain.resolver import apply_action, get_legal_actions
from solo_wargame_ai.domain.state import CurrentActivation, create_initial_game_state
from solo_wargame_ai.domain.units import (
    BritishMorale,
    GermanUnitStatus,
    RevealedGermanUnitState,
)
from solo_wargame_ai.interactive.action_view import build_ui_action_selection
from solo_wargame_ai.interactive.state_view import build_state_view
from solo_wargame_ai.io.mission_loader import load_mission

MISSION3_PATH = (
    Path(__file__).resolve().parents[2]
    / "configs"
    / "missions"
    / "mission_03_secure_the_building.toml"
)


def test_action_views_have_stable_per_state_ids_and_player_labels(mission) -> None:
    state = create_initial_game_state(mission, seed=0)
    legal_actions = get_legal_actions(state)

    first_selection = build_ui_action_selection(state, legal_actions)
    second_selection = build_ui_action_selection(state, legal_actions)

    assert [view.id for view in first_selection.action_views] == [
        view.id for view in second_selection.action_views
    ]
    assert first_selection.action_views[0].label == "Activate Rifle Squad A"
    assert first_selection.action_views[0].payload == {
        "kind": "select_british_unit",
        "unit_id": "rifle_squad_a",
    }
    assert first_selection.action_views[0].hints == {
        "kind": "select_british_unit",
        "unit_id": "rifle_squad_a",
    }


def test_state_view_exposes_map_units_markers_decision_and_legal_actions(mission) -> None:
    state = create_initial_game_state(mission, seed=0)
    legal_actions = get_legal_actions(state)

    view = build_state_view(state, legal_actions)

    assert view["mission"]["id"] == "mission_01_secure_the_woods_1"
    assert view["turn"] == 1
    assert view["phase"] == "british"
    assert view["pending_decision"] == {
        "kind": "choose_british_unit",
        "label": "Choose a British unit",
    }
    assert view["current_activation"] is None
    assert view["terminal_outcome"] is None
    assert len(view["map"]["hexes"]) == 10
    assert view["units"]["british"][0]["display_name"] == "Rifle Squad A"
    assert view["units"]["british"][0]["counter_label"] == "A"
    assert view["units"]["british"][0]["morale"] == "normal"
    assert view["units"]["british"][0]["morale_label"] == "Normal"
    assert view["units"]["unresolved_markers"] == [
        {"id": "qm_1", "counter_label": "?1", "coord": {"q": 0, "r": 1}},
    ]
    assert [action["label"] for action in view["legal_actions"]] == [
        "Activate Rifle Squad A",
        "Activate Rifle Squad B",
    ]
    assert [
        (entry["unit_id"], entry["kinds"], entry["shortcut_action_id"] is not None)
        for entry in view["affordances"]["british_units"]
    ] == [
        ("rifle_squad_a", ["select_british_unit"], True),
        ("rifle_squad_b", ["select_british_unit"], True),
    ]
    assert view["affordances"]["acting_side"] == "british"
    assert view["affordances"]["active_british_unit_id"] is None
    assert view["affordances"]["advance_destinations"] == []


def test_action_labels_follow_staged_activation_context(mission) -> None:
    state = create_initial_game_state(mission, seed=0)
    state = apply_action(state, SelectBritishUnitAction(unit_id="rifle_squad_a"))

    double_selection = build_ui_action_selection(state, get_legal_actions(state))
    assert [action.label for action in double_selection.action_views] == [
        "Keep double 4: Fire + Take cover",
        "Reroll the double",
    ]
    assert double_selection.action_views[0].hints == {
        "kind": "resolve_double_choice",
        "choice": "keep",
        "die_value": 4,
        "orders": ["fire", "take_cover"],
        "order_labels": ["Fire", "Take cover"],
    }

    state = apply_action(
        state,
        ResolveDoubleChoiceAction(choice=DoubleChoiceOption.KEEP),
    )
    die_selection = build_ui_action_selection(state, get_legal_actions(state))
    assert die_selection.action_views[-1].payload == {
        "kind": "discard_activation_roll",
    }
    assert die_selection.action_views[-1].label == "Discard the roll"


def test_die_choice_labels_and_hints_explain_orders_chart_rows_after_reroll(mission) -> None:
    state = create_initial_game_state(mission, seed=0)
    state = apply_action(state, SelectBritishUnitAction(unit_id="rifle_squad_a"))
    state = apply_action(
        state,
        ResolveDoubleChoiceAction(choice=DoubleChoiceOption.REROLL),
    )

    die_selection = build_ui_action_selection(state, get_legal_actions(state))

    assert [action.label for action in die_selection.action_views] == [
        "Use die 1: Rally + Grenade attack",
        "Use die 3: Advance + Take cover",
        "Discard the roll",
    ]
    assert die_selection.action_views[0].hints == {
        "kind": "select_activation_die",
        "die_value": 1,
        "orders": ["rally", "grenade_attack"],
        "order_labels": ["Rally", "Grenade attack"],
    }
    assert die_selection.action_views[1].hints == {
        "kind": "select_activation_die",
        "die_value": 3,
        "orders": ["advance", "take_cover"],
        "order_labels": ["Advance", "Take cover"],
    }


def test_current_activation_view_exposes_roll_options(mission) -> None:
    state = create_initial_game_state(mission, seed=0)
    state = apply_action(state, SelectBritishUnitAction(unit_id="rifle_squad_a"))

    view = build_state_view(state, get_legal_actions(state))

    assert view["current_activation"]["roll"] == [4, 4]
    assert view["current_activation"]["roll_options"] == [
        {
            "die_value": 4,
            "orders": ["fire", "take_cover"],
            "order_labels": ["Fire", "Take cover"],
        },
    ]


def test_order_hint_fallback_keeps_action_views_safe_without_activation(mission) -> None:
    state = create_initial_game_state(mission, seed=0)

    selection = build_ui_action_selection(
        state,
        (
            ResolveDoubleChoiceAction(choice=DoubleChoiceOption.KEEP),
            SelectActivationDieAction(die_value=1),
        ),
    )

    assert [action.label for action in selection.action_views] == [
        "Keep the double",
        "Use die 1",
    ]
    assert selection.action_views[0].hints == {
        "kind": "resolve_double_choice",
        "choice": "keep",
    }
    assert selection.action_views[1].hints == {
        "kind": "select_activation_die",
        "die_value": 1,
    }


def test_advance_action_view_exposes_target_coordinate_hint(mission) -> None:
    state = create_initial_game_state(mission, seed=0)
    action = AdvanceAction(destination=HexCoord(q=0, r=2))

    selection = build_ui_action_selection(state, (action,))

    assert selection.action_views[0].label == "Advance to (0, 2)"
    assert selection.action_views[0].hints == {
        "kind": "advance",
        "target_coord": {"q": 0, "r": 2},
    }


def test_state_view_exposes_advance_destination_affordance(mission) -> None:
    state = create_initial_game_state(mission, seed=0)
    action = AdvanceAction(destination=HexCoord(q=0, r=2))

    view = build_state_view(state, (action,))

    advance_affordance = view["affordances"]["advance_destinations"][0]
    assert advance_affordance["coord"] == {"q": 0, "r": 2}
    assert advance_affordance["kinds"] == ["advance"]
    assert advance_affordance["action_ids"] == [view["legal_actions"][0]["id"]]
    assert advance_affordance["shortcut_action_id"] == view["legal_actions"][0]["id"]


def test_discard_action_label_is_plain_language(mission) -> None:
    state = create_initial_game_state(mission, seed=0)

    selection = build_ui_action_selection(state, (DiscardActivationRollAction(),))

    assert selection.action_views[0].label == "Discard the roll"


def test_low_morale_order_execution_label_and_hints_explain_first_order_limit(
    mission,
) -> None:
    state = _low_morale_order_execution_state(mission)

    selection = build_ui_action_selection(state, get_legal_actions(state))

    assert [action.label for action in selection.action_views] == [
        "Execute only first order: Rally",
        "Skip activation",
    ]
    assert selection.action_views[0].hints == {
        "kind": "choose_order_execution",
        "choice": "first_order_only",
        "restriction": {
            "kind": "low_morale",
            "message": "Low morale: only the first order can be executed.",
            "short_message": "low morale: only Rally available",
            "available_orders": ["rally"],
            "available_order_labels": ["Rally"],
            "unavailable_orders": ["grenade_attack"],
            "unavailable_order_labels": ["Grenade attack"],
        },
    }
    assert selection.action_views[1].hints["restriction"]["kind"] == "low_morale"


def test_low_morale_die_choice_label_explains_only_first_order_is_available(mission) -> None:
    state = _low_morale_die_choice_state(mission)

    selection = build_ui_action_selection(state, get_legal_actions(state))

    assert selection.action_views[0].label == (
        "Use die 1: Rally + Grenade attack (low morale: only Rally available)"
    )
    assert selection.action_views[0].hints["restriction"] == {
        "kind": "low_morale",
        "message": "Low morale: only the first order can be executed.",
        "short_message": "low morale: only Rally available",
        "available_orders": ["rally"],
        "available_order_labels": ["Rally"],
        "unavailable_orders": ["grenade_attack"],
        "unavailable_order_labels": ["Grenade attack"],
    }


def test_current_activation_view_exposes_active_unit_morale(mission) -> None:
    state = _low_morale_order_execution_state(mission)

    view = build_state_view(state, get_legal_actions(state))

    assert view["current_activation"]["active_unit_id"] == "rifle_squad_a"
    assert view["current_activation"]["active_unit_morale"] == "low"
    assert view["current_activation"]["active_unit_morale_label"] == "Low"
    assert view["current_activation"]["restrictions"] == [
        {
            "kind": "low_morale",
            "message": "Low morale: only the first order can be executed.",
        },
    ]
    assert view["current_activation"]["roll_options"][0]["restriction"] == {
        "kind": "low_morale",
        "message": "Low morale: only the first order can be executed.",
        "short_message": "low morale: only Rally available",
        "available_orders": ["rally"],
        "available_order_labels": ["Rally"],
        "unavailable_orders": ["grenade_attack"],
        "unavailable_order_labels": ["Grenade attack"],
    }


def test_state_view_exposes_revealed_german_facing(mission) -> None:
    state = create_initial_game_state(mission, seed=0)
    state = replace(
        state,
        german_units={
            "qm_1": RevealedGermanUnitState(
                unit_id="qm_1",
                unit_class="light_machine_gun",
                position=HexCoord(0, 1),
                facing=HexDirection.DOWN_RIGHT,
                status=GermanUnitStatus.ACTIVE,
            ),
        },
        unresolved_markers={},
    )

    view = build_state_view(state, get_legal_actions(state))

    assert view["units"]["german"] == [
        {
            "id": "qm_1",
            "unit_class": "light_machine_gun",
            "display_name": "Light machine gun QM 1",
            "counter_label": "LMG 1",
            "coord": {"q": 0, "r": 1},
            "facing": "down_right",
            "facing_label": "Down right",
            "status": "active",
            "activated": False,
        },
    ]


def test_state_view_exposes_generic_counter_labels_for_mission3_units() -> None:
    mission = load_mission(MISSION3_PATH)
    state = create_initial_game_state(mission, seed=0)

    view = build_state_view(state, get_legal_actions(state))

    assert [unit["counter_label"] for unit in view["units"]["british"]] == ["A", "B", "C"]


def test_state_view_exposes_numbered_counter_labels_for_multiple_revealed_germans() -> None:
    mission = load_mission(MISSION3_PATH)
    state = create_initial_game_state(mission, seed=0)
    state = replace(
        state,
        german_units={
            "qm_1": RevealedGermanUnitState(
                unit_id="qm_1",
                unit_class="heavy_machine_gun",
                position=HexCoord(-1, 2),
                facing=HexDirection.DOWN,
                status=GermanUnitStatus.ACTIVE,
            ),
            "qm_2": RevealedGermanUnitState(
                unit_id="qm_2",
                unit_class="light_machine_gun",
                position=HexCoord(0, 1),
                facing=HexDirection.DOWN_LEFT,
                status=GermanUnitStatus.ACTIVE,
            ),
            "qm_3": RevealedGermanUnitState(
                unit_id="qm_3",
                unit_class="german_rifle_squad",
                position=HexCoord(1, 1),
                facing=HexDirection.DOWN_RIGHT,
                status=GermanUnitStatus.ACTIVE,
            ),
        },
        unresolved_markers={},
    )

    view = build_state_view(state, get_legal_actions(state))

    assert [unit["counter_label"] for unit in view["units"]["german"]] == [
        "HMG 1",
        "LMG 2",
        "GRS 3",
    ]


def test_state_view_exposes_distinct_hidden_marker_counter_labels_for_mission3() -> None:
    mission = load_mission(MISSION3_PATH)
    state = create_initial_game_state(mission, seed=0)

    view = build_state_view(state, get_legal_actions(state))

    assert [
        (marker["id"], marker["counter_label"])
        for marker in view["units"]["unresolved_markers"]
    ] == [
        ("qm_1", "?1"),
        ("qm_2", "?2"),
        ("qm_3", "?3"),
    ]


def test_german_target_action_labels_match_numbered_counter_labels() -> None:
    mission = load_mission(MISSION3_PATH)
    state = create_initial_game_state(mission, seed=0)
    state = replace(
        state,
        german_units={
            "qm_2": RevealedGermanUnitState(
                unit_id="qm_2",
                unit_class="light_machine_gun",
                position=HexCoord(0, 1),
                facing=HexDirection.DOWN_LEFT,
                status=GermanUnitStatus.ACTIVE,
            ),
        },
        unresolved_markers={},
    )

    selection = build_ui_action_selection(
        state,
        (
            FireAction(target_unit_id="qm_2"),
            GrenadeAttackAction(target_unit_id="qm_2"),
            SelectGermanUnitAction(unit_id="qm_2"),
        ),
    )

    assert [action.label for action in selection.action_views] == [
        "Fire at LMG 2",
        "Grenade attack LMG 2",
        "Resolve German fire: LMG 2",
    ]


def test_state_view_groups_german_target_affordances_without_ambiguous_shortcut() -> None:
    mission = load_mission(MISSION3_PATH)
    state = create_initial_game_state(mission, seed=0)
    state = replace(
        state,
        german_units={
            "qm_2": RevealedGermanUnitState(
                unit_id="qm_2",
                unit_class="light_machine_gun",
                position=HexCoord(0, 1),
                facing=HexDirection.DOWN_LEFT,
                status=GermanUnitStatus.ACTIVE,
            ),
        },
        unresolved_markers={},
    )

    view = build_state_view(
        state,
        (
            FireAction(target_unit_id="qm_2"),
            GrenadeAttackAction(target_unit_id="qm_2"),
        ),
    )

    german_affordance = view["affordances"]["german_units"][0]
    assert german_affordance["unit_id"] == "qm_2"
    assert german_affordance["kinds"] == ["fire", "grenade_attack"]
    assert german_affordance["shortcut_action_id"] is None


def test_state_view_exposes_unambiguous_german_select_shortcut() -> None:
    mission = load_mission(MISSION3_PATH)
    state = create_initial_game_state(mission, seed=0)

    view = build_state_view(state, (SelectGermanUnitAction(unit_id="qm_1"),))

    german_affordance = view["affordances"]["german_units"][0]
    assert german_affordance["unit_id"] == "qm_1"
    assert german_affordance["kinds"] == ["select_german_unit"]
    assert german_affordance["shortcut_action_id"] == view["legal_actions"][0]["id"]


def test_state_view_groups_scout_marker_affordances_without_ambiguous_shortcut(
    mission,
) -> None:
    state = create_initial_game_state(mission, seed=0)

    view = build_state_view(
        state,
        (
            ScoutAction(marker_id="qm_1", facing=HexDirection.DOWN),
            ScoutAction(marker_id="qm_1", facing=HexDirection.DOWN_LEFT),
        ),
    )

    marker_affordance = view["affordances"]["hidden_markers"][0]
    assert marker_affordance["marker_id"] == "qm_1"
    assert marker_affordance["kinds"] == ["scout", "scout"]
    assert marker_affordance["shortcut_action_id"] is None


def test_state_view_exposes_unambiguous_scout_marker_shortcut(mission) -> None:
    state = create_initial_game_state(mission, seed=0)

    view = build_state_view(state, (ScoutAction(marker_id="qm_1"),))

    marker_affordance = view["affordances"]["hidden_markers"][0]
    assert marker_affordance["marker_id"] == "qm_1"
    assert marker_affordance["kinds"] == ["scout"]
    assert marker_affordance["shortcut_action_id"] == view["legal_actions"][0]["id"]


def test_both_orders_label_makes_commitment_explicit(mission) -> None:
    state = replace(
        create_initial_game_state(mission, seed=0),
        pending_decision=ChooseOrderExecutionContext(),
        current_activation=CurrentActivation(
            active_unit_id="rifle_squad_a",
            roll=(5, 2),
            selected_die=5,
        ),
    )

    selection = build_ui_action_selection(
        state,
        (ChooseOrderExecutionAction(choice=OrderExecutionChoice.BOTH_ORDERS),),
    )

    assert selection.action_views[0].label == "Commit to both orders: Fire, then Advance"
    assert selection.action_views[0].hints["commitment"] == {
        "kind": "both_orders",
        "message": "Both orders are committed before resolving the first order.",
        "order_labels": ["Fire", "Advance"],
    }


def _low_morale_order_execution_state(mission):
    return _low_morale_activation_state(
        mission,
        pending_decision=ChooseOrderExecutionContext(),
        selected_die=1,
    )


def _low_morale_die_choice_state(mission):
    return _low_morale_activation_state(
        mission,
        pending_decision=ChooseActivationDieContext(),
        selected_die=None,
    )


def _low_morale_activation_state(mission, *, pending_decision, selected_die):
    state = create_initial_game_state(mission, seed=0)
    low_morale_unit = replace(
        state.british_units["rifle_squad_a"],
        morale=BritishMorale.LOW,
    )
    return replace(
        state,
        british_units={**state.british_units, "rifle_squad_a": low_morale_unit},
        pending_decision=pending_decision,
        current_activation=CurrentActivation(
            active_unit_id="rifle_squad_a",
            roll=(1, 2),
            selected_die=selected_die,
        ),
    )
