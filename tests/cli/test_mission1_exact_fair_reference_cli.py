from __future__ import annotations

import json
from pathlib import Path

from solo_wargame_ai.cli import mission1_exact_fair_reference
from solo_wargame_ai.eval.mission1_exact_fair_ceiling import (
    MISSION1_FAIR_AGENT_CONTRACT,
    MISSION1_PRESERVED_ANCHORS,
    SCRATCH_ESTIMATE_EVIDENCE_ONLY,
    Mission1ChanceTableSummary,
    Mission1ExactFairSmokeResult,
    Mission1ExactFairSolveResult,
)


def _smoke_result() -> Mission1ExactFairSmokeResult:
    return Mission1ExactFairSmokeResult(
        mission_id="mission_01_secure_the_woods_1",
        mode="smoke",
        fair_agent_contract=MISSION1_FAIR_AGENT_CONTRACT,
        preserved_anchors=MISSION1_PRESERVED_ANCHORS,
        scratch_estimate_evidence_only=SCRATCH_ESTIMATE_EVIDENCE_ONLY,
        chance_tables=Mission1ChanceTableSummary(
            activation_roll_probability_mass=1.0,
            reveal_probability_mass=1.0,
        ),
        root_action_count=2,
        first_root_action="SelectBritishUnitAction(unit_id='rifle_squad_a')",
        first_root_action_outcome_mass=1.0,
        solved_state_count=22,
    )


def _exact_result() -> Mission1ExactFairSolveResult:
    return Mission1ExactFairSolveResult(
        mission_id="mission_01_secure_the_woods_1",
        mode="exact",
        fair_agent_contract=MISSION1_FAIR_AGENT_CONTRACT,
        preserved_anchors=MISSION1_PRESERVED_ANCHORS,
        scratch_estimate_evidence_only=SCRATCH_ESTIMATE_EVIDENCE_ONLY,
        fair_ceiling=0.945,
        root_action_values=(
            ("SelectBritishUnitAction(unit_id='rifle_squad_a')", 0.945),
            ("SelectBritishUnitAction(unit_id='rifle_squad_b')", 0.941),
        ),
        solved_state_count=1234,
    )


def test_cli_defaults_to_smoke_and_writes_preservation_outputs(
    monkeypatch,
    tmp_path,
    capsys,
) -> None:
    mission = object()
    smoke_result = _smoke_result()

    def fake_load_mission(path: Path) -> object:
        assert path == mission1_exact_fair_reference.MISSION_PATH
        return mission

    def fake_run_smoke(
        received_mission: object,
        *,
        seed: int,
        progress_interval_sec: float,
    ) -> Mission1ExactFairSmokeResult:
        assert received_mission is mission
        assert seed == 0
        assert progress_interval_sec == 5.0
        return smoke_result

    def fail_exact(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("exact solve should not run in default smoke mode")

    monkeypatch.setattr(
        mission1_exact_fair_reference,
        "load_mission",
        fake_load_mission,
    )
    monkeypatch.setattr(
        mission1_exact_fair_reference,
        "run_mission1_exact_fair_smoke",
        fake_run_smoke,
    )
    monkeypatch.setattr(
        mission1_exact_fair_reference,
        "solve_mission1_exact_fair_ceiling",
        fail_exact,
    )

    output_path = tmp_path / "reports" / "mission1-exact-smoke.txt"
    json_output_path = tmp_path / "reports" / "mission1-exact-smoke.json"

    exit_code = mission1_exact_fair_reference.main(
        [
            "--output",
            str(output_path),
            "--json-output",
            str(json_output_path),
        ],
    )

    assert exit_code == 0
    stdout = capsys.readouterr().out
    assert "Mission 1 exact fair reference" in stdout
    assert "mode: smoke" in stdout
    assert "reference_status: smoke_probe_only" in stdout
    assert "Preserved historical Mission 1 anchors:" in stdout
    assert "scratch_estimate_status: evidence-only" in stdout
    assert "Operator handoff:" in stdout
    assert (
        ".venv/bin/python -m solo_wargame_ai.cli.mission1_exact_fair_reference --mode exact"
        in stdout
    )
    assert output_path.read_text(encoding="utf-8") == stdout

    payload = json.loads(json_output_path.read_text(encoding="utf-8"))
    assert payload["mode"] == "smoke"
    assert payload["reference_status"] == "smoke_probe_only"
    assert payload["operator_handoff"]["smoke_default"] is True
    assert payload["smoke_probe"]["root_action_count"] == 2
    assert payload["preserved_historical_anchors"] == list(MISSION1_PRESERVED_ANCHORS)
    assert (
        payload["operator_handoff"]["exact_solve_command"]
        == ".venv/bin/python -m solo_wargame_ai.cli.mission1_exact_fair_reference --mode exact"
    )


def test_cli_exact_mode_keeps_exact_reference_separate_from_preserved_anchors(
    monkeypatch,
    tmp_path,
    capsys,
) -> None:
    mission = object()
    exact_result = _exact_result()

    def fake_load_mission(path: Path) -> object:
        assert path == mission1_exact_fair_reference.MISSION_PATH
        return mission

    def fake_solve_exact(
        received_mission: object,
        *,
        seed: int,
        progress_interval_sec: float,
    ) -> Mission1ExactFairSolveResult:
        assert received_mission is mission
        assert seed == 0
        assert progress_interval_sec == 5.0
        return exact_result

    def fail_smoke(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("smoke helper should not run in exact mode")

    monkeypatch.setattr(
        mission1_exact_fair_reference,
        "load_mission",
        fake_load_mission,
    )
    monkeypatch.setattr(
        mission1_exact_fair_reference,
        "solve_mission1_exact_fair_ceiling",
        fake_solve_exact,
    )
    monkeypatch.setattr(
        mission1_exact_fair_reference,
        "run_mission1_exact_fair_smoke",
        fail_smoke,
    )

    output_path = tmp_path / "reports" / "mission1-exact-report.txt"
    json_output_path = tmp_path / "reports" / "mission1-exact-report.json"

    exit_code = mission1_exact_fair_reference.main(
        [
            "--mode",
            "exact",
            "--output",
            str(output_path),
            "--json-output",
            str(json_output_path),
        ],
    )

    assert exit_code == 0
    stdout = capsys.readouterr().out
    assert "mode: exact" in stdout
    assert "reference_status: operator_run_exact_reference" in stdout
    assert "Exact fair reference result:" in stdout
    assert "fair_ceiling: 0.945000000000" in stdout
    assert "Preserved historical Mission 1 anchors:" in stdout
    assert "RolloutSearchAgent 195/200 preserved oracle/planner-like reference" in stdout
    assert output_path.read_text(encoding="utf-8") == stdout

    payload = json.loads(json_output_path.read_text(encoding="utf-8"))
    assert payload["mode"] == "exact"
    assert payload["reference_status"] == "operator_run_exact_reference"
    assert payload["exact_result"]["fair_ceiling"] == 0.945
    assert payload["exact_result"]["root_action_values"][0]["action"] == (
        "SelectBritishUnitAction(unit_id='rifle_squad_a')"
    )
    assert "RolloutSearchAgent 195/200" in payload["preserved_historical_anchors"][3]
