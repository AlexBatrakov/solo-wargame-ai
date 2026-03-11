"""Thin Mission 3 operator surface for the active comparison packet."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from solo_wargame_ai.eval.mission3_comparison import (
    MISSION3_BENCHMARK_SEEDS,
    MISSION3_SMOKE_SEEDS,
    Mission3Comparison,
    run_mission3_random_floor_comparison,
    run_mission3_smoke_comparison,
)
from solo_wargame_ai.io.mission_loader import load_mission

MISSION_PATH = (
    Path(__file__).resolve().parents[3]
    / "configs"
    / "missions"
    / "mission_03_secure_the_building.toml"
)


def build_parser() -> argparse.ArgumentParser:
    """Build the thin Mission 3 comparison rerun surface."""

    parser = argparse.ArgumentParser(
        description="Run the Mission 3 local comparison surface.",
    )
    parser.add_argument(
        "--mode",
        choices=("smoke", "benchmark"),
        required=True,
        help="Run the 16-seed smoke floor or the 200-seed benchmark floor.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optionally write the rendered report to a plain-text file.",
    )
    return parser


def format_mission3_report(
    *,
    mode: str,
    comparison: Mission3Comparison,
) -> str:
    """Render a Mission-3-only report around the local comparison table."""

    lines = [
        "Mission 3 comparison surface",
        f"mode: {mode}",
        f"mission: {MISSION_PATH.name}",
        "comparison_scope: mission3_only",
        f"seed_alias: {_format_seed_alias(comparison.seeds)}",
        f"seed_set: {_format_seed_set(comparison.seeds)}",
        "",
        "Metrics table:",
        comparison.report_table,
        "",
        "Surface status:",
        "random_floor_ready: yes",
        "pending_agents: heuristic, rollout-search",
        "pending_delivery: Delivery B",
        "mission1_anchor_surface: preserved separately",
    ]
    return "\n".join(lines)


def _format_seed_alias(seeds: tuple[int, ...]) -> str:
    if seeds == MISSION3_SMOKE_SEEDS:
        return "mission3_smoke"
    if seeds == MISSION3_BENCHMARK_SEEDS:
        return "mission3_benchmark"
    return "custom"


def _format_seed_set(seeds: tuple[int, ...]) -> str:
    if not seeds:
        return "empty"
    if seeds == tuple(range(len(seeds))):
        return f"{seeds[0]}..{seeds[-1]} ({len(seeds)} seeds)"
    return f"{seeds!r} ({len(seeds)} seeds)"


def main(argv: Sequence[str] | None = None) -> int:
    """Run the requested Mission 3 local comparison surface and print the report."""

    args = build_parser().parse_args(argv)
    mission = load_mission(MISSION_PATH)

    if args.mode == "smoke":
        comparison = run_mission3_smoke_comparison(mission)
    else:
        comparison = run_mission3_random_floor_comparison(
            mission,
            seeds=MISSION3_BENCHMARK_SEEDS,
        )

    report = format_mission3_report(mode=args.mode, comparison=comparison)
    print(report)

    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(f"{report}\n", encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
