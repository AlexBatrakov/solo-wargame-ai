from __future__ import annotations

from pathlib import Path

from solo_wargame_ai.eval import exact_guided_heuristic_comparison as comparison_module
from solo_wargame_ai.eval.mission_summary import MissionSummary

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


def _summary(
    *,
    mission_path: Path,
    policy_agent_name: str,
    policy_seed_wins: int,
    policy_seed_ratio: float,
    policy_vs_seed_ceiling_ratio: float,
    policy_full_probability_value: float | None = None,
    policy_vs_exact_ceiling_ratio: float | None = None,
    exact_full_space_ceiling: float | None = None,
    exact_equivalent_200: float | None = None,
    exact_fixed_seed_ceiling_wins: int | None = None,
    exact_fixed_seed_ratio: float | None = None,
    exact_fixed_seed_source: str | None = None,
    exact_fixed_seed_caveat: str | None = None,
) -> MissionSummary:
    return MissionSummary(
        mission_id=mission_path.stem,
        mission_path=mission_path,
        benchmark_seed_count=200,
        exact_full_space_ceiling=exact_full_space_ceiling,
        exact_equivalent_200=exact_equivalent_200,
        exact_artifact_dir=Path(".project_local/artifacts") / f"{mission_path.stem}_exact_artifact",
        exact_artifact_has_action_values=exact_fixed_seed_ceiling_wins is not None,
        exact_fixed_seed_ceiling_wins=exact_fixed_seed_ceiling_wins,
        exact_fixed_seed_ceiling_ratio=exact_fixed_seed_ratio,
        exact_fixed_seed_source=exact_fixed_seed_source,
        exact_fixed_seed_caveat=exact_fixed_seed_caveat,
        policy_artifact_dir=None,
        policy_agent_name=policy_agent_name,
        policy_full_probability_value=policy_full_probability_value,
        policy_equivalent_200=(
            None if policy_full_probability_value is None else policy_full_probability_value * 200.0
        ),
        policy_seed_wins=policy_seed_wins,
        policy_seed_ratio=policy_seed_ratio,
        policy_vs_exact_ceiling_ratio=policy_vs_exact_ceiling_ratio,
        policy_vs_seed_ceiling_ratio=policy_vs_seed_ceiling_ratio,
    )


def test_build_exact_guided_heuristic_comparison_preserves_historical_anchor_framing(
    monkeypatch,
) -> None:
    summaries = iter(
        (
            _summary(
                mission_path=MISSION1_PATH,
                policy_agent_name="heuristic",
                policy_seed_wins=157,
                policy_seed_ratio=0.785,
                policy_vs_seed_ceiling_ratio=0.844086,
                policy_full_probability_value=0.752396519423,
                policy_vs_exact_ceiling_ratio=0.792123,
                exact_full_space_ceiling=0.949848647767,
                exact_equivalent_200=189.96973,
                exact_fixed_seed_ceiling_wins=186,
                exact_fixed_seed_ratio=0.93,
                exact_fixed_seed_source="artifact_action_values",
            ),
            _summary(
                mission_path=MISSION1_PATH,
                policy_agent_name="exact-guided-heuristic",
                policy_seed_wins=177,
                policy_seed_ratio=0.885,
                policy_vs_seed_ceiling_ratio=0.951613,
                policy_full_probability_value=0.875290156699,
                policy_vs_exact_ceiling_ratio=0.921505,
                exact_full_space_ceiling=0.949848647767,
                exact_equivalent_200=189.96973,
                exact_fixed_seed_ceiling_wins=186,
                exact_fixed_seed_ratio=0.93,
                exact_fixed_seed_source="artifact_action_values",
            ),
            _summary(
                mission_path=MISSION2_PATH,
                policy_agent_name="heuristic",
                policy_seed_wins=71,
                policy_seed_ratio=0.355,
                policy_vs_seed_ceiling_ratio=71 / 131,
                exact_full_space_ceiling=0.598931044695,
                exact_equivalent_200=119.786209,
                exact_fixed_seed_ceiling_wins=131,
                exact_fixed_seed_ratio=0.655,
                exact_fixed_seed_source="known_anchor_artifact_replay",
                exact_fixed_seed_caveat=(
                    "Strong working anchor from artifact-backed deterministic replay via "
                    "reconstructed Q*(s,a), but not yet as fully locked down as Mission 1 "
                    "186/200."
                ),
            ),
            _summary(
                mission_path=MISSION2_PATH,
                policy_agent_name="exact-guided-heuristic",
                policy_seed_wins=94,
                policy_seed_ratio=0.47,
                policy_vs_seed_ceiling_ratio=94 / 131,
                exact_full_space_ceiling=0.598931044695,
                exact_equivalent_200=119.786209,
                exact_fixed_seed_ceiling_wins=131,
                exact_fixed_seed_ratio=0.655,
                exact_fixed_seed_source="known_anchor_artifact_replay",
                exact_fixed_seed_caveat=(
                    "Strong working anchor from artifact-backed deterministic replay via "
                    "reconstructed Q*(s,a), but not yet as fully locked down as Mission 1 "
                    "186/200."
                ),
            ),
        ),
    )
    calls: list[dict[str, object]] = []

    def fake_build_mission_summary(**kwargs):  # type: ignore[no-untyped-def]
        calls.append(kwargs)
        return next(summaries)

    monkeypatch.setattr(
        comparison_module,
        "build_mission_summary",
        fake_build_mission_summary,
    )

    comparison = comparison_module.build_exact_guided_heuristic_comparison()

    assert [call["agent_name"] for call in calls] == [
        "heuristic",
        "exact-guided-heuristic",
        "heuristic",
        "exact-guided-heuristic",
    ]
    assert comparison.mission1.historical_anchor_wins == 157
    assert comparison.mission1.historical_vs_anchor_seed_delta == 0
    assert comparison.mission1.promoted_vs_anchor_seed_delta == 20
    assert comparison.mission1.promoted_vs_historical_seed_delta == 20
    assert comparison.mission2.historical_anchor_wins == 71
    assert comparison.mission2.comparison_mode == "benchmark_light"
    assert comparison.mission2.promoted_vs_historical_seed_delta == 23

    payload = comparison.to_payload()
    assert payload["mission2"]["promoted_summary"]["policy_seed_wins"] == 94
    assert payload["mission2"]["promoted_vs_historical_seed_delta"] == 23
    assert len(payload["successor_progression_summary"]) == 4


def test_format_exact_guided_heuristic_report_includes_exact_and_transfer_fields() -> None:
    mission1 = comparison_module.MissionHeuristicComparison(
        comparison_mode="exact_backed",
        mission_path=MISSION1_PATH,
        historical_agent_name="heuristic",
        historical_anchor_wins=157,
        historical_summary=_summary(
            mission_path=MISSION1_PATH,
            policy_agent_name="heuristic",
            policy_seed_wins=157,
            policy_seed_ratio=0.785,
            policy_vs_seed_ceiling_ratio=0.844086,
            policy_full_probability_value=0.752396519423,
            policy_vs_exact_ceiling_ratio=0.792123,
            exact_full_space_ceiling=0.949848647767,
            exact_equivalent_200=189.96973,
            exact_fixed_seed_ceiling_wins=186,
            exact_fixed_seed_ratio=0.93,
            exact_fixed_seed_source="artifact_action_values",
        ),
        promoted_agent_name="exact-guided-heuristic",
        promoted_summary=_summary(
            mission_path=MISSION1_PATH,
            policy_agent_name="exact-guided-heuristic",
            policy_seed_wins=177,
            policy_seed_ratio=0.885,
            policy_vs_seed_ceiling_ratio=0.951613,
            policy_full_probability_value=0.875290156699,
            policy_vs_exact_ceiling_ratio=0.921505,
            exact_full_space_ceiling=0.949848647767,
            exact_equivalent_200=189.96973,
            exact_fixed_seed_ceiling_wins=186,
            exact_fixed_seed_ratio=0.93,
            exact_fixed_seed_source="artifact_action_values",
        ),
        historical_vs_anchor_seed_delta=0,
        promoted_vs_anchor_seed_delta=20,
        promoted_vs_historical_seed_delta=20,
    )
    mission2 = comparison_module.MissionHeuristicComparison(
        comparison_mode="benchmark_light",
        mission_path=MISSION2_PATH,
        historical_agent_name="heuristic",
        historical_anchor_wins=71,
        historical_summary=_summary(
            mission_path=MISSION2_PATH,
            policy_agent_name="heuristic",
            policy_seed_wins=71,
            policy_seed_ratio=0.355,
            policy_vs_seed_ceiling_ratio=71 / 131,
            exact_full_space_ceiling=0.598931044695,
            exact_equivalent_200=119.786209,
            exact_fixed_seed_ceiling_wins=131,
            exact_fixed_seed_ratio=0.655,
            exact_fixed_seed_source="known_anchor_artifact_replay",
            exact_fixed_seed_caveat=(
                "Strong working anchor from artifact-backed deterministic replay via "
                "reconstructed Q*(s,a), but not yet as fully locked down as Mission 1 "
                "186/200."
            ),
        ),
        promoted_agent_name="exact-guided-heuristic",
        promoted_summary=_summary(
            mission_path=MISSION2_PATH,
            policy_agent_name="exact-guided-heuristic",
            policy_seed_wins=94,
            policy_seed_ratio=0.47,
            policy_vs_seed_ceiling_ratio=94 / 131,
            exact_full_space_ceiling=0.598931044695,
            exact_equivalent_200=119.786209,
            exact_fixed_seed_ceiling_wins=131,
            exact_fixed_seed_ratio=0.655,
            exact_fixed_seed_source="known_anchor_artifact_replay",
            exact_fixed_seed_caveat=(
                "Strong working anchor from artifact-backed deterministic replay via "
                "reconstructed Q*(s,a), but not yet as fully locked down as Mission 1 "
                "186/200."
            ),
        ),
        historical_vs_anchor_seed_delta=0,
        promoted_vs_anchor_seed_delta=23,
        promoted_vs_historical_seed_delta=23,
    )
    comparison = comparison_module.ExactGuidedHeuristicComparison(
        comparison_kind=comparison_module.EXACT_GUIDED_COMPARISON_KIND,
        benchmark_seeds=tuple(range(200)),
        mission1=mission1,
        mission2=mission2,
        successor_progression_summary=comparison_module.SUCCESSOR_PROGRESSION_SUMMARY,
    )

    report = comparison_module.format_exact_guided_heuristic_report(comparison)

    assert "Mission 1 exact-backed comparison:" in report
    assert "preserved_historical_anchor: heuristic 157/200" in report
    assert "promoted_policy_seed_wins: 177/200" in report
    assert "promoted_policy_vs_exact_ceiling_ratio: 0.921505" in report
    assert "Mission 2 benchmark-light transfer:" in report
    assert "promoted_policy_seed_wins: 94/200" in report
    assert "promoted_policy_seed_ratio: 0.470000" in report
    assert "promoted_policy_vs_seed_ceiling_ratio: 0.717557" in report
    assert "exact_fixed_seed_caveat: Strong working anchor" in report
    assert "Successor progression summary:" in report
