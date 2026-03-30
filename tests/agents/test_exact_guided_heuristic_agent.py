from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from solo_wargame_ai.agents.exact_guided_heuristic_agent import (
    ExactGuidedHeuristicAgent,
)
from solo_wargame_ai.domain.actions import (
    AdvanceAction,
    SelectActivationDieAction,
)
from solo_wargame_ai.domain.decision_context import (
    ChooseActivationDieContext,
    ChooseOrderParameterContext,
)
from solo_wargame_ai.domain.enums import HexDirection
from solo_wargame_ai.domain.hexgrid import HexCoord
from solo_wargame_ai.domain.mission import OrderName
from solo_wargame_ai.domain.resolver import get_legal_actions
from solo_wargame_ai.domain.state import (
    CurrentActivation,
    create_initial_game_state,
    validate_game_state,
)
from solo_wargame_ai.domain.units import GermanUnitStatus, RevealedGermanUnitState
from solo_wargame_ai.eval.mission_summary import benchmark_policy_seed_wins
from solo_wargame_ai.io import load_mission

MISSION1_PATH = (
    Path(__file__).resolve().parents[2]
    / "configs"
    / "missions"
    / "mission_01_secure_the_woods_1.toml"
)
MISSION2_PATH = (
    Path(__file__).resolve().parents[2]
    / "configs"
    / "missions"
    / "mission_02_secure_the_woods_2.toml"
)


def test_exact_guided_heuristic_prefers_the_promoted_mission1_left_lane_opening() -> None:
    mission = load_mission(MISSION1_PATH)
    base_state = create_initial_game_state(mission, seed=0)
    state = replace(
        base_state,
        british_units={
            **base_state.british_units,
            "rifle_squad_a": replace(
                base_state.british_units["rifle_squad_a"],
                position=HexCoord(-1, 3),
            ),
            "rifle_squad_b": replace(
                base_state.british_units["rifle_squad_b"],
                position=HexCoord(0, 3),
            ),
        },
        pending_decision=ChooseOrderParameterContext(
            order=OrderName.ADVANCE,
            order_index=0,
        ),
        current_activation=CurrentActivation(
            active_unit_id="rifle_squad_b",
            roll=(2, 2),
            selected_die=2,
            planned_orders=(OrderName.ADVANCE, OrderName.SCOUT),
            next_order_index=0,
        ),
    )
    validate_game_state(state)

    legal_actions = get_legal_actions(state)
    selected_action = ExactGuidedHeuristicAgent().select_action(state, legal_actions)

    assert selected_action == AdvanceAction(destination=HexCoord(-1, 3))


def test_exact_guided_heuristic_prefers_the_mined_mission2_die_choice() -> None:
    mission = load_mission(MISSION2_PATH)
    base_state = create_initial_game_state(mission, seed=0)
    state = replace(
        base_state,
        british_units={
            **base_state.british_units,
            "rifle_squad_a": replace(
                base_state.british_units["rifle_squad_a"],
                position=HexCoord(0, 2),
                cover=0,
            ),
            "rifle_squad_b": replace(
                base_state.british_units["rifle_squad_b"],
                position=HexCoord(0, 3),
                cover=0,
            ),
        },
        german_units={
            "qm_2": RevealedGermanUnitState(
                unit_id="qm_2",
                unit_class="light_machine_gun",
                position=HexCoord(-1, 2),
                facing=HexDirection.DOWN_RIGHT,
                status=GermanUnitStatus.ACTIVE,
            ),
        },
        unresolved_markers={
            "qm_1": base_state.unresolved_markers["qm_1"],
        },
        pending_decision=ChooseActivationDieContext(),
        current_activation=CurrentActivation(
            active_unit_id="rifle_squad_b",
            roll=(2, 6),
        ),
    )
    validate_game_state(state)

    legal_actions = get_legal_actions(state)
    selected_action = ExactGuidedHeuristicAgent().select_action(state, legal_actions)

    assert selected_action == SelectActivationDieAction(die_value=6)


def test_exact_guided_heuristic_matches_the_promoted_benchmark_snapshots() -> None:
    mission1_wins = benchmark_policy_seed_wins(
        mission_path=MISSION1_PATH,
        build_agent=lambda: ExactGuidedHeuristicAgent(),
        seeds=tuple(range(200)),
    )
    mission2_wins = benchmark_policy_seed_wins(
        mission_path=MISSION2_PATH,
        build_agent=lambda: ExactGuidedHeuristicAgent(),
        seeds=tuple(range(200)),
    )

    assert mission1_wins == 177
    assert mission2_wins == 94
