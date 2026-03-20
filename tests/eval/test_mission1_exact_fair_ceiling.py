from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from solo_wargame_ai.domain.state import TerminalOutcome, create_initial_game_state
from solo_wargame_ai.eval.mission1_exact_fair_ceiling import (
    MISSION1_FAIR_AGENT_CONTRACT,
    SCRATCH_ESTIMATE_EVIDENCE_ONLY,
    _build_mission1_exact_fair_solver,
    run_mission1_exact_fair_smoke,
)
from solo_wargame_ai.io.mission_loader import load_mission

MISSION_PATH = (
    Path(__file__).resolve().parents[2]
    / "configs"
    / "missions"
    / "mission_01_secure_the_woods_1.toml"
)


def test_mission1_exact_solver_chance_tables_and_root_outcomes_are_normalized() -> None:
    mission = load_mission(MISSION_PATH)
    solver = _build_mission1_exact_fair_solver(mission, progress_interval_sec=3600.0)

    assert solver.chance_tables.activation_roll_probability_mass == pytest.approx(1.0)
    assert solver.chance_tables.reveal_probability_mass == pytest.approx(1.0)

    root_key = solver.root_state_key(seed=0)
    root_actions = solver.legal_actions_for(root_key)
    assert root_actions
    for action in root_actions:
        assert solver.action_outcome_mass(root_key, action) == pytest.approx(1.0)


def test_mission1_exact_solver_terminal_values_are_stable() -> None:
    mission = load_mission(MISSION_PATH)
    solver = _build_mission1_exact_fair_solver(mission, progress_interval_sec=3600.0)
    root_state = create_initial_game_state(mission, seed=0)

    victory_key = solver.intern_state(
        replace(root_state, terminal_outcome=TerminalOutcome.VICTORY),
    )
    defeat_key = solver.intern_state(
        replace(root_state, terminal_outcome=TerminalOutcome.DEFEAT),
    )

    assert solver.value(victory_key) == 1.0
    assert solver.value(defeat_key) == 0.0


def test_mission1_exact_fair_smoke_mode_is_bounded_and_contract_explicit() -> None:
    mission = load_mission(MISSION_PATH)

    result = run_mission1_exact_fair_smoke(
        mission,
        seed=0,
        progress_interval_sec=3600.0,
    )

    assert result.mode == "smoke"
    assert result.root_action_count > 0
    assert result.first_root_action_outcome_mass == pytest.approx(1.0)
    assert result.chance_tables.activation_roll_probability_mass == pytest.approx(1.0)
    assert result.chance_tables.reveal_probability_mass == pytest.approx(1.0)
    assert result.scratch_estimate_evidence_only == pytest.approx(
        SCRATCH_ESTIMATE_EVIDENCE_ONLY,
    )
    assert any("player-visible" in line for line in MISSION1_FAIR_AGENT_CONTRACT)
    assert any("rng_state" in line for line in MISSION1_FAIR_AGENT_CONTRACT)
