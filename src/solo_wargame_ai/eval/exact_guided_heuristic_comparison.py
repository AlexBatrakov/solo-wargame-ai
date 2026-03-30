"""Comparison helpers for the promoted exact-guided heuristic successor."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from solo_wargame_ai.agents.exact_guided_heuristic_agent import (
    ExactGuidedHeuristicAgent,
)
from solo_wargame_ai.agents.heuristic_agent import HeuristicAgent
from solo_wargame_ai.eval.benchmark import PHASE3_BENCHMARK_SEEDS

from .mission_summary import MissionSummary, build_mission_summary

MISSION1_PATH = (
    Path(__file__).resolve().parents[3]
    / "configs"
    / "missions"
    / "mission_01_secure_the_woods_1.toml"
)
MISSION2_PATH = (
    Path(__file__).resolve().parents[3]
    / "configs"
    / "missions"
    / "mission_02_secure_the_woods_2.toml"
)

EXACT_GUIDED_COMPARISON_KIND = "exact_guided_heuristic_comparison"
MISSION1_HISTORICAL_HEURISTIC_WINS = 157
MISSION2_HISTORICAL_HEURISTIC_WINS = 71
SUCCESSOR_PROGRESSION_SUMMARY: tuple[str, ...] = (
    "HeuristicAgent remains the preserved historical baseline on both missions.",
    (
        "ExactGuidedHeuristicAgent productizes the stable Mission 1 endgame, "
        "opening, and compact-table line without rewriting the historical "
        "baseline."
    ),
    (
        "Mission 2 transfer stays deliberately narrow: only the later scout and "
        "activation-die refinements that survived full reruns are absorbed into "
        "the shared promoted candidate."
    ),
    (
        "The local round ladder is assimilated only as one successor surface and "
        "this comparison report, not as a tracked per-round agent family."
    ),
)


def _seed_delta(summary: MissionSummary, anchor_wins: int) -> int | None:
    if summary.policy_seed_wins is None:
        return None
    return summary.policy_seed_wins - anchor_wins


def _pairwise_seed_delta(
    historical_summary: MissionSummary,
    promoted_summary: MissionSummary,
) -> int | None:
    if historical_summary.policy_seed_wins is None or promoted_summary.policy_seed_wins is None:
        return None
    return promoted_summary.policy_seed_wins - historical_summary.policy_seed_wins


@dataclass(frozen=True, slots=True)
class MissionHeuristicComparison:
    """One mission-local historical-vs-promoted heuristic view."""

    comparison_mode: str
    mission_path: Path
    historical_agent_name: str
    historical_anchor_wins: int
    historical_summary: MissionSummary
    promoted_agent_name: str
    promoted_summary: MissionSummary
    historical_vs_anchor_seed_delta: int | None
    promoted_vs_anchor_seed_delta: int | None
    promoted_vs_historical_seed_delta: int | None

    def to_payload(self) -> dict[str, object]:
        return {
            "comparison_mode": self.comparison_mode,
            "mission_path": str(self.mission_path),
            "historical_agent_name": self.historical_agent_name,
            "historical_anchor_wins": self.historical_anchor_wins,
            "historical_vs_anchor_seed_delta": self.historical_vs_anchor_seed_delta,
            "promoted_agent_name": self.promoted_agent_name,
            "promoted_vs_anchor_seed_delta": self.promoted_vs_anchor_seed_delta,
            "promoted_vs_historical_seed_delta": self.promoted_vs_historical_seed_delta,
            "historical_summary": self.historical_summary.to_payload(),
            "promoted_summary": self.promoted_summary.to_payload(),
        }


@dataclass(frozen=True, slots=True)
class ExactGuidedHeuristicComparison:
    """Top-level promoted-handoff comparison surface."""

    comparison_kind: str
    benchmark_seeds: tuple[int, ...]
    mission1: MissionHeuristicComparison
    mission2: MissionHeuristicComparison
    successor_progression_summary: tuple[str, ...]

    def to_payload(self) -> dict[str, object]:
        return {
            "comparison_kind": self.comparison_kind,
            "benchmark_seeds": list(self.benchmark_seeds),
            "mission1": self.mission1.to_payload(),
            "mission2": self.mission2.to_payload(),
            "successor_progression_summary": list(self.successor_progression_summary),
        }


def build_exact_guided_heuristic_comparison(
    *,
    mission1_path: Path = MISSION1_PATH,
    mission2_path: Path = MISSION2_PATH,
    mission1_exact_artifact_dir: Path | None = None,
    mission1_historical_policy_artifact_dir: Path | None = None,
    mission1_promoted_policy_artifact_dir: Path | None = None,
    mission2_exact_artifact_dir: Path | None = None,
    mission2_historical_policy_artifact_dir: Path | None = None,
    mission2_promoted_policy_artifact_dir: Path | None = None,
    seed_stop: int = len(PHASE3_BENCHMARK_SEEDS),
) -> ExactGuidedHeuristicComparison:
    """Build the promoted successor comparison on tracked mission-summary seams."""

    mission1_historical_summary = build_mission_summary(
        mission_path=mission1_path,
        exact_artifact_dir=mission1_exact_artifact_dir,
        policy_artifact_dir=mission1_historical_policy_artifact_dir,
        build_agent=lambda: HeuristicAgent(),
        agent_name=HeuristicAgent.name,
        seed_stop=seed_stop,
    )
    mission1_promoted_summary = build_mission_summary(
        mission_path=mission1_path,
        exact_artifact_dir=mission1_exact_artifact_dir,
        policy_artifact_dir=mission1_promoted_policy_artifact_dir,
        build_agent=lambda: ExactGuidedHeuristicAgent(),
        agent_name=ExactGuidedHeuristicAgent.name,
        seed_stop=seed_stop,
    )
    mission2_historical_summary = build_mission_summary(
        mission_path=mission2_path,
        exact_artifact_dir=mission2_exact_artifact_dir,
        policy_artifact_dir=mission2_historical_policy_artifact_dir,
        build_agent=lambda: HeuristicAgent(),
        agent_name=HeuristicAgent.name,
        seed_stop=seed_stop,
    )
    mission2_promoted_summary = build_mission_summary(
        mission_path=mission2_path,
        exact_artifact_dir=mission2_exact_artifact_dir,
        policy_artifact_dir=mission2_promoted_policy_artifact_dir,
        build_agent=lambda: ExactGuidedHeuristicAgent(),
        agent_name=ExactGuidedHeuristicAgent.name,
        seed_stop=seed_stop,
    )

    return ExactGuidedHeuristicComparison(
        comparison_kind=EXACT_GUIDED_COMPARISON_KIND,
        benchmark_seeds=tuple(range(seed_stop)),
        mission1=MissionHeuristicComparison(
            comparison_mode="exact_backed",
            mission_path=Path(mission1_path),
            historical_agent_name=HeuristicAgent.name,
            historical_anchor_wins=MISSION1_HISTORICAL_HEURISTIC_WINS,
            historical_summary=mission1_historical_summary,
            promoted_agent_name=ExactGuidedHeuristicAgent.name,
            promoted_summary=mission1_promoted_summary,
            historical_vs_anchor_seed_delta=_seed_delta(
                mission1_historical_summary,
                MISSION1_HISTORICAL_HEURISTIC_WINS,
            ),
            promoted_vs_anchor_seed_delta=_seed_delta(
                mission1_promoted_summary,
                MISSION1_HISTORICAL_HEURISTIC_WINS,
            ),
            promoted_vs_historical_seed_delta=_pairwise_seed_delta(
                mission1_historical_summary,
                mission1_promoted_summary,
            ),
        ),
        mission2=MissionHeuristicComparison(
            comparison_mode="benchmark_light",
            mission_path=Path(mission2_path),
            historical_agent_name=HeuristicAgent.name,
            historical_anchor_wins=MISSION2_HISTORICAL_HEURISTIC_WINS,
            historical_summary=mission2_historical_summary,
            promoted_agent_name=ExactGuidedHeuristicAgent.name,
            promoted_summary=mission2_promoted_summary,
            historical_vs_anchor_seed_delta=_seed_delta(
                mission2_historical_summary,
                MISSION2_HISTORICAL_HEURISTIC_WINS,
            ),
            promoted_vs_anchor_seed_delta=_seed_delta(
                mission2_promoted_summary,
                MISSION2_HISTORICAL_HEURISTIC_WINS,
            ),
            promoted_vs_historical_seed_delta=_pairwise_seed_delta(
                mission2_historical_summary,
                mission2_promoted_summary,
            ),
        ),
        successor_progression_summary=SUCCESSOR_PROGRESSION_SUMMARY,
    )


def format_exact_guided_heuristic_report(
    comparison: ExactGuidedHeuristicComparison,
) -> str:
    """Render the promoted successor comparison/reporting surface."""

    lines = [
        "Promoted exact-guided heuristic comparison",
        f"comparison_kind: {comparison.comparison_kind}",
        "comparison_scope: mission1_exact_backed + mission2_benchmark_light",
        f"benchmark_seed_set: {_format_seed_set(comparison.benchmark_seeds)}",
        "",
        "Mission 1 exact-backed comparison:",
        *_format_mission_section(comparison.mission1),
        "",
        "Mission 2 benchmark-light transfer:",
        *_format_mission_section(comparison.mission2),
        "",
        "Successor progression summary:",
        *[
            f"progression_{index}: {line}"
            for index, line in enumerate(
                comparison.successor_progression_summary,
                start=1,
            )
        ],
    ]
    return "\n".join(lines)


def _format_mission_section(comparison: MissionHeuristicComparison) -> tuple[str, ...]:
    promoted = comparison.promoted_summary
    historical = comparison.historical_summary
    lines = [
        f"comparison_mode: {comparison.comparison_mode}",
        f"mission_id: {promoted.mission_id}",
        f"mission_path: {comparison.mission_path}",
        (
            "preserved_historical_anchor: "
            f"{comparison.historical_agent_name} "
            f"{comparison.historical_anchor_wins}/{promoted.benchmark_seed_count}"
        ),
    ]

    if promoted.exact_artifact_dir is not None:
        lines.append(f"exact_artifact_dir: {promoted.exact_artifact_dir}")
    lines.append(
        f"exact_artifact_has_action_values: {promoted.exact_artifact_has_action_values}",
    )
    if promoted.exact_full_space_ceiling is not None:
        lines.append(f"exact_full_space_ceiling: {promoted.exact_full_space_ceiling:.12f}")
    if promoted.exact_equivalent_200 is not None:
        lines.append(f"exact_equivalent_200: {promoted.exact_equivalent_200:.6f}")
    if promoted.exact_fixed_seed_ceiling_wins is not None:
        lines.append(
            "exact_fixed_seed_ceiling: "
            f"{promoted.exact_fixed_seed_ceiling_wins}/{promoted.benchmark_seed_count}",
        )
    if promoted.exact_fixed_seed_ceiling_ratio is not None:
        lines.append(
            (
                "exact_fixed_seed_ceiling_ratio: "
                f"{promoted.exact_fixed_seed_ceiling_ratio:.6f}"
            ),
        )
    if promoted.exact_fixed_seed_source is not None:
        lines.append(f"exact_fixed_seed_source: {promoted.exact_fixed_seed_source}")
    if promoted.exact_fixed_seed_caveat is not None:
        lines.append(f"exact_fixed_seed_caveat: {promoted.exact_fixed_seed_caveat}")

    if historical.policy_artifact_dir is not None:
        lines.append(f"historical_policy_artifact_dir: {historical.policy_artifact_dir}")
    if promoted.policy_artifact_dir is not None:
        lines.append(f"promoted_policy_artifact_dir: {promoted.policy_artifact_dir}")
    lines.extend(
        (
            f"historical_policy_agent_name: {historical.policy_agent_name}",
            f"historical_policy_seed_wins: {_format_seed_wins(historical)}",
            f"historical_policy_seed_ratio: {_format_ratio(historical.policy_seed_ratio)}",
            (
                "historical_policy_vs_seed_ceiling_ratio: "
                f"{_format_ratio(historical.policy_vs_seed_ceiling_ratio)}"
            ),
            (
                "historical_vs_preserved_anchor_seed_delta: "
                f"{_format_signed_int(comparison.historical_vs_anchor_seed_delta)}"
            ),
            f"promoted_policy_agent_name: {promoted.policy_agent_name}",
            f"promoted_policy_seed_wins: {_format_seed_wins(promoted)}",
            f"promoted_policy_seed_ratio: {_format_ratio(promoted.policy_seed_ratio)}",
            (
                "promoted_policy_vs_seed_ceiling_ratio: "
                f"{_format_ratio(promoted.policy_vs_seed_ceiling_ratio)}"
            ),
            (
                "promoted_vs_preserved_anchor_seed_delta: "
                f"{_format_signed_int(comparison.promoted_vs_anchor_seed_delta)}"
            ),
            (
                "promoted_vs_historical_seed_delta: "
                f"{_format_signed_int(comparison.promoted_vs_historical_seed_delta)}"
            ),
        ),
    )
    if historical.policy_full_probability_value is not None:
        lines.append(
            "historical_policy_full_probability_value: "
            f"{historical.policy_full_probability_value:.12f}",
        )
    if historical.policy_vs_exact_ceiling_ratio is not None:
        lines.append(
            "historical_policy_vs_exact_ceiling_ratio: "
            f"{historical.policy_vs_exact_ceiling_ratio:.6f}",
        )
    if promoted.policy_full_probability_value is not None:
        lines.append(
            "promoted_policy_full_probability_value: "
            f"{promoted.policy_full_probability_value:.12f}",
        )
    if promoted.policy_vs_exact_ceiling_ratio is not None:
        lines.append(
            "promoted_policy_vs_exact_ceiling_ratio: "
            f"{promoted.policy_vs_exact_ceiling_ratio:.6f}",
        )
    return tuple(lines)


def _format_seed_set(seeds: tuple[int, ...]) -> str:
    if not seeds:
        return "empty"
    if seeds == tuple(range(len(seeds))):
        return f"{seeds[0]}..{seeds[-1]} ({len(seeds)} seeds)"
    return f"{seeds!r} ({len(seeds)} seeds)"


def _format_seed_wins(summary: MissionSummary) -> str:
    if summary.policy_seed_wins is None:
        return "n/a"
    return f"{summary.policy_seed_wins}/{summary.benchmark_seed_count}"


def _format_ratio(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.6f}"


def _format_signed_int(value: int | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:+d}"


__all__ = [
    "EXACT_GUIDED_COMPARISON_KIND",
    "ExactGuidedHeuristicComparison",
    "MISSION1_HISTORICAL_HEURISTIC_WINS",
    "MISSION1_PATH",
    "MISSION2_HISTORICAL_HEURISTIC_WINS",
    "MISSION2_PATH",
    "MissionHeuristicComparison",
    "SUCCESSOR_PROGRESSION_SUMMARY",
    "build_exact_guided_heuristic_comparison",
    "format_exact_guided_heuristic_report",
]
