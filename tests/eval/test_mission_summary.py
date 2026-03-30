from __future__ import annotations

from pathlib import Path

import pytest

from solo_wargame_ai.eval import mission_summary as mission_summary_module

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


def test_build_mission_summary_uses_known_mission2_anchor_without_local_artifacts(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        mission_summary_module,
        "default_exact_artifact_dir",
        lambda _mission_path: tmp_path / "missing-artifact",
    )

    summary = mission_summary_module.build_mission_summary(
        mission_path=MISSION2_PATH,
        seed_stop=200,
    )

    assert summary.exact_artifact_dir is None
    assert summary.exact_artifact_has_action_values is False
    assert summary.exact_full_space_ceiling == pytest.approx(0.598931044695)
    assert summary.exact_equivalent_200 == pytest.approx(119.786209)
    assert summary.exact_fixed_seed_ceiling_wins == 131
    assert summary.exact_fixed_seed_ceiling_ratio == pytest.approx(0.655)
    assert summary.exact_fixed_seed_source == "known_anchor_artifact_replay"
    assert "Strong working anchor" in (summary.exact_fixed_seed_caveat or "")

    report = mission_summary_module.format_mission_summary_report(summary)
    assert "mission_id: mission_02_secure_the_woods_2" in report
    assert "exact_fixed_seed_source: known_anchor_artifact_replay" in report
    assert "exact_fixed_seed_ceiling: 131/200" in report


def test_build_mission_summary_combines_artifact_policy_and_seed_surfaces(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    sentinel_agent = object()
    exact_artifact_dir = tmp_path / "exact-artifact"
    policy_artifact_dir = tmp_path / "policy-artifact"

    class FakeExactArtifact:
        def __init__(self, **_kwargs) -> None:  # type: ignore[no-untyped-def]
            self.metadata = {"root_value": 0.75}

        def has_action_values(self) -> bool:
            return True

        def close(self) -> None:
            return None

    def fake_exact_seed_wins(**kwargs) -> int:  # type: ignore[no-untyped-def]
        assert kwargs["mission_path"] == MISSION1_PATH
        assert kwargs["seeds"] == tuple(range(200))
        return 150

    def fake_read_policy_audit_stats(artifact_dir: Path) -> dict[str, object]:
        assert artifact_dir == policy_artifact_dir
        return {
            "policy_root_value": 0.6,
            "agent_name": "policy-audit-agent",
        }

    def fake_benchmark_policy_seed_wins(**kwargs) -> int:  # type: ignore[no-untyped-def]
        assert kwargs["mission_path"] == MISSION1_PATH
        assert kwargs["build_agent"]() is sentinel_agent
        assert kwargs["seeds"] == tuple(range(200))
        return 120

    monkeypatch.setattr(
        mission_summary_module,
        "ExactArtifact",
        FakeExactArtifact,
    )
    monkeypatch.setattr(
        mission_summary_module,
        "deterministic_exact_seed_wins_from_artifact",
        fake_exact_seed_wins,
    )
    monkeypatch.setattr(
        mission_summary_module,
        "read_policy_audit_stats",
        fake_read_policy_audit_stats,
    )
    monkeypatch.setattr(
        mission_summary_module,
        "benchmark_policy_seed_wins",
        fake_benchmark_policy_seed_wins,
    )

    summary = mission_summary_module.build_mission_summary(
        mission_path=MISSION1_PATH,
        exact_artifact_dir=exact_artifact_dir,
        policy_artifact_dir=policy_artifact_dir,
        build_agent=lambda: sentinel_agent,
        seed_stop=200,
    )

    assert summary.exact_artifact_dir == exact_artifact_dir
    assert summary.exact_artifact_has_action_values is True
    assert summary.exact_full_space_ceiling == pytest.approx(0.75)
    assert summary.exact_equivalent_200 == pytest.approx(150.0)
    assert summary.exact_fixed_seed_ceiling_wins == 150
    assert summary.exact_fixed_seed_source == "artifact_action_values"
    assert summary.policy_artifact_dir == policy_artifact_dir
    assert summary.policy_agent_name == "policy-audit-agent"
    assert summary.policy_full_probability_value == pytest.approx(0.6)
    assert summary.policy_equivalent_200 == pytest.approx(120.0)
    assert summary.policy_seed_wins == 120
    assert summary.policy_seed_ratio == pytest.approx(0.6)
    assert summary.policy_vs_exact_ceiling_ratio == pytest.approx(0.8)
    assert summary.policy_vs_seed_ceiling_ratio == pytest.approx(0.8)


def test_build_mission_summary_falls_back_to_known_seed_anchor_when_action_rows_absent(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    exact_artifact_dir = tmp_path / "exact-artifact"

    class FakeExactArtifact:
        def __init__(self, **_kwargs) -> None:  # type: ignore[no-untyped-def]
            self.metadata = {"root_value": 0.598931044695}

        def has_action_values(self) -> bool:
            return False

        def close(self) -> None:
            return None

    def fail_solver_replay(**_kwargs) -> int:  # type: ignore[no-untyped-def]
        raise AssertionError("full solver replay should stay disabled in this path")

    monkeypatch.setattr(
        mission_summary_module,
        "ExactArtifact",
        FakeExactArtifact,
    )
    monkeypatch.setattr(
        mission_summary_module,
        "deterministic_exact_seed_wins_from_solver",
        fail_solver_replay,
    )

    summary = mission_summary_module.build_mission_summary(
        mission_path=MISSION2_PATH,
        exact_artifact_dir=exact_artifact_dir,
        seed_stop=200,
        allow_known_anchor=True,
        allow_full_solver_replay=False,
    )

    assert summary.exact_artifact_dir == exact_artifact_dir
    assert summary.exact_artifact_has_action_values is False
    assert summary.exact_full_space_ceiling == pytest.approx(0.598931044695)
    assert summary.exact_fixed_seed_ceiling_wins == 131
    assert summary.exact_fixed_seed_source == "known_anchor_artifact_replay"
    assert "Strong working anchor" in (summary.exact_fixed_seed_caveat or "")
