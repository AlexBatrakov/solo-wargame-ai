"""Thin manual entrypoint for accepted Phase 3 baseline comparisons."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from solo_wargame_ai.eval.benchmark import (
    PHASE3_BENCHMARK_SEEDS,
    BenchmarkComparison,
    run_random_vs_heuristic_comparison,
    run_smoke_comparison,
)
from solo_wargame_ai.eval.metrics import EpisodeMetricsDelta
from solo_wargame_ai.io.mission_loader import load_mission

MISSION_PATH = (
    Path(__file__).resolve().parents[3]
    / "configs"
    / "missions"
    / "mission_01_secure_the_woods_1.toml"
)


def build_parser() -> argparse.ArgumentParser:
    """Build the small Phase 3 manual rerun surface."""

    parser = argparse.ArgumentParser(
        description="Run the accepted Phase 3 random-vs-heuristic comparisons.",
    )
    parser.add_argument(
        "--mode",
        choices=("smoke", "benchmark"),
        required=True,
        help="Run the 16-seed smoke comparison or the 200-seed benchmark.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optionally write the rendered report to a plain-text file.",
    )
    return parser


def format_phase3_report(
    *,
    mode: str,
    comparison: BenchmarkComparison,
) -> str:
    """Render a human-readable summary around the accepted benchmark table."""

    lines = [
        "Phase 3 baseline comparison",
        f"mode: {mode}",
        f"mission: {MISSION_PATH.name}",
        f"seed_set: {_format_seed_set(comparison.seeds)}",
        "",
        "Metrics table:",
        comparison.report_table,
        "",
        "Signed metric deltas (heuristic - random):",
        _format_metric_deltas(comparison.metric_deltas),
    ]
    return "\n".join(lines)


def _format_seed_set(seeds: tuple[int, ...]) -> str:
    if not seeds:
        return "empty"
    if seeds == tuple(range(len(seeds))):
        return f"{seeds[0]}..{seeds[-1]} ({len(seeds)} seeds)"
    return f"{seeds!r} ({len(seeds)} seeds)"


def _format_metric_deltas(deltas: EpisodeMetricsDelta) -> str:
    return "\n".join(
        (
            f"episode_count          {deltas.episode_count_delta:+d}",
            f"victory_count          {deltas.victory_count_delta:+d}",
            f"defeat_count           {deltas.defeat_count_delta:+d}",
            f"win_rate               {deltas.win_rate_delta:+.3f}",
            f"defeat_rate            {deltas.defeat_rate_delta:+.3f}",
            f"mean_terminal_turn     {deltas.mean_terminal_turn_delta:+.3f}",
            f"mean_resolved_markers  {deltas.mean_resolved_marker_count_delta:+.3f}",
            f"mean_removed_german    {deltas.mean_removed_german_count_delta:+.3f}",
            f"mean_player_decisions  {deltas.mean_player_decision_count_delta:+.3f}",
        ),
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Run the requested accepted comparison and print the stable report."""

    args = build_parser().parse_args(argv)
    mission = load_mission(MISSION_PATH)

    if args.mode == "smoke":
        comparison = run_smoke_comparison(mission)
    else:
        comparison = run_random_vs_heuristic_comparison(
            mission,
            seeds=PHASE3_BENCHMARK_SEEDS,
        )

    report = format_phase3_report(mode=args.mode, comparison=comparison)
    print(report)

    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(f"{report}\n", encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
