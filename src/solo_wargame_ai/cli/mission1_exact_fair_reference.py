"""Thin Mission-1-local operator surface for the exact fair reference."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from solo_wargame_ai.eval.mission1_exact_fair_ceiling import (
    MISSION1_DEFAULT_MISSION_PATH,
    run_mission1_exact_fair_smoke,
    solve_mission1_exact_fair_ceiling,
)
from solo_wargame_ai.eval.mission1_exact_fair_reference_reporting import (
    format_mission1_exact_fair_reference_report,
    mission1_exact_fair_reference_payload,
)
from solo_wargame_ai.io.mission_loader import load_mission

MISSION_PATH = (
    Path(__file__).resolve().parents[3]
    / "configs"
    / "missions"
    / "mission_01_secure_the_woods_1.toml"
)


def build_parser() -> argparse.ArgumentParser:
    """Build the Mission 1 exact fair-reference operator CLI."""

    parser = argparse.ArgumentParser(
        description="Run the Mission 1 exact fair-reference smoke or exact workflow.",
    )
    parser.add_argument(
        "--mode",
        choices=("smoke", "exact"),
        default="smoke",
        help="Smoke is the safe default; exact remains explicit opt-in.",
    )
    parser.add_argument(
        "--mission",
        type=Path,
        default=MISSION_PATH,
        help="Path to Mission 1 TOML. Defaults to the tracked Mission 1 config.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Initial RNG seed for root state construction.",
    )
    parser.add_argument(
        "--progress-interval-sec",
        type=float,
        default=5.0,
        help="Progress print interval; smoke remains bounded even if provided.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optionally write the plain-text report to a file.",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        help="Optionally write the machine-readable payload to JSON.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the Mission 1 exact fair-reference workflow and print the report."""

    args = build_parser().parse_args(argv)
    mission_path = args.mission
    if mission_path == MISSION1_DEFAULT_MISSION_PATH:
        mission_path = MISSION_PATH
    mission = load_mission(mission_path)

    if args.mode == "smoke":
        result = run_mission1_exact_fair_smoke(
            mission,
            seed=args.seed,
            progress_interval_sec=args.progress_interval_sec,
        )
    else:
        result = solve_mission1_exact_fair_ceiling(
            mission,
            seed=args.seed,
            progress_interval_sec=args.progress_interval_sec,
        )

    report = format_mission1_exact_fair_reference_report(result)
    print(report)

    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(f"{report}\n", encoding="utf-8")

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(
            json.dumps(
                mission1_exact_fair_reference_payload(result),
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
