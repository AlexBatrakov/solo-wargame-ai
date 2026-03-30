from __future__ import annotations

import json
from pathlib import Path

from solo_wargame_ai.cli import mission_summary
from solo_wargame_ai.eval.mission_summary import MissionSummary

MISSION1_PATH = (
    Path(__file__).resolve().parents[2]
    / "configs"
    / "missions"
    / "mission_01_secure_the_woods_1.toml"
)


def test_cli_prints_report_and_writes_outputs(
    monkeypatch,
    tmp_path,
    capsys,
) -> None:
    sentinel_agent = object()
    summary = MissionSummary(
        mission_id="mission_01_secure_the_woods_1",
        mission_path=MISSION1_PATH,
        benchmark_seed_count=200,
        exact_full_space_ceiling=0.75,
        exact_equivalent_200=150.0,
        exact_artifact_dir=tmp_path / "exact-artifact",
        exact_artifact_has_action_values=True,
        exact_fixed_seed_ceiling_wins=150,
        exact_fixed_seed_ceiling_ratio=0.75,
        exact_fixed_seed_source="artifact_action_values",
        exact_fixed_seed_caveat=None,
        policy_artifact_dir=tmp_path / "policy-artifact",
        policy_agent_name="loaded-agent",
        policy_full_probability_value=0.6,
        policy_equivalent_200=120.0,
        policy_seed_wins=120,
        policy_seed_ratio=0.6,
        policy_vs_exact_ceiling_ratio=0.8,
        policy_vs_seed_ceiling_ratio=0.8,
    )

    def fake_validate_agent_loader_spec(spec, *, require_loader: bool) -> None:  # type: ignore[no-untyped-def]
        assert spec.agent_factory == "pkg:make_agent"
        assert require_loader is True

    def fake_build_explicit_agent_factory(spec):  # type: ignore[no-untyped-def]
        assert spec.agent_factory == "pkg:make_agent"
        return lambda: sentinel_agent

    def fake_resolve_explicit_agent_name(spec, *, agent_factory):  # type: ignore[no-untyped-def]
        assert spec.agent_factory == "pkg:make_agent"
        assert agent_factory() is sentinel_agent
        return "loaded-agent"

    def fake_build_mission_summary(**kwargs):  # type: ignore[no-untyped-def]
        assert kwargs["mission_path"] == MISSION1_PATH
        assert kwargs["build_agent"]() is sentinel_agent
        assert kwargs["agent_name"] == "loaded-agent"
        return summary

    def fake_format_mission_summary_report(received_summary: MissionSummary) -> str:
        assert received_summary is summary
        return "report text"

    monkeypatch.setattr(
        mission_summary,
        "validate_agent_loader_spec",
        fake_validate_agent_loader_spec,
    )
    monkeypatch.setattr(
        mission_summary,
        "build_explicit_agent_factory",
        fake_build_explicit_agent_factory,
    )
    monkeypatch.setattr(
        mission_summary,
        "resolve_explicit_agent_name",
        fake_resolve_explicit_agent_name,
    )
    monkeypatch.setattr(
        mission_summary,
        "build_mission_summary",
        fake_build_mission_summary,
    )
    monkeypatch.setattr(
        mission_summary,
        "format_mission_summary_report",
        fake_format_mission_summary_report,
    )

    output_path = tmp_path / "reports" / "summary.txt"
    json_output_path = tmp_path / "reports" / "summary.json"

    exit_code = mission_summary.main(
        [
            "--mission",
            str(MISSION1_PATH),
            "--agent-factory",
            "pkg:make_agent",
            "--output",
            str(output_path),
            "--json-output",
            str(json_output_path),
        ],
    )

    assert exit_code == 0
    assert capsys.readouterr().out == "report text\n"
    assert output_path.read_text(encoding="utf-8") == "report text\n"

    payload = json.loads(json_output_path.read_text(encoding="utf-8"))
    assert payload["mission_id"] == summary.mission_id
    assert payload["exact_fixed_seed_source"] == "artifact_action_values"
    assert payload["policy_seed_wins"] == 120


def test_cli_json_output_preserves_known_anchor_seed_source(
    monkeypatch,
    tmp_path,
    capsys,
) -> None:
    summary = MissionSummary(
        mission_id="mission_02_secure_the_woods_2",
        mission_path=MISSION1_PATH,
        benchmark_seed_count=200,
        exact_full_space_ceiling=0.598931044695,
        exact_equivalent_200=119.786209,
        exact_artifact_dir=None,
        exact_artifact_has_action_values=False,
        exact_fixed_seed_ceiling_wins=131,
        exact_fixed_seed_ceiling_ratio=0.655,
        exact_fixed_seed_source="known_anchor_artifact_replay",
        exact_fixed_seed_caveat=(
            "Strong working anchor from artifact-backed deterministic replay via reconstructed "
            "Q*(s,a), but not yet as fully locked down as Mission 1 186/200."
        ),
        policy_artifact_dir=None,
        policy_agent_name=None,
        policy_full_probability_value=None,
        policy_equivalent_200=None,
        policy_seed_wins=None,
        policy_seed_ratio=None,
        policy_vs_exact_ceiling_ratio=None,
        policy_vs_seed_ceiling_ratio=None,
    )

    monkeypatch.setattr(
        mission_summary,
        "build_mission_summary",
        lambda **_kwargs: summary,
    )
    monkeypatch.setattr(
        mission_summary,
        "format_mission_summary_report",
        lambda _summary: "anchor report",
    )

    json_output_path = tmp_path / "reports" / "summary.json"

    exit_code = mission_summary.main(
        [
            "--mission",
            str(MISSION1_PATH),
            "--json-output",
            str(json_output_path),
        ],
    )

    assert exit_code == 0
    assert capsys.readouterr().out == "anchor report\n"

    payload = json.loads(json_output_path.read_text(encoding="utf-8"))
    assert payload["exact_fixed_seed_source"] == "known_anchor_artifact_replay"
    assert "Strong working anchor" in payload["exact_fixed_seed_caveat"]
