"""Thin operator surface for the promoted exact-guided heuristic comparison."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from solo_wargame_ai.eval.exact_guided_heuristic_comparison import (
    build_exact_guided_heuristic_comparison,
    format_exact_guided_heuristic_report,
)


def build_parser() -> argparse.ArgumentParser:
    """Build the promoted exact-guided heuristic comparison CLI."""

    parser = argparse.ArgumentParser(
        description="Run the promoted exact-guided heuristic comparison surface.",
    )
    parser.add_argument("--seed-stop", type=int, default=200)
    parser.add_argument("--mission1-exact-artifact-dir", type=Path, default=None)
    parser.add_argument(
        "--mission1-historical-policy-artifact-dir",
        type=Path,
        default=None,
    )
    parser.add_argument(
        "--mission1-promoted-policy-artifact-dir",
        type=Path,
        default=None,
    )
    parser.add_argument("--mission2-exact-artifact-dir", type=Path, default=None)
    parser.add_argument(
        "--mission2-historical-policy-artifact-dir",
        type=Path,
        default=None,
    )
    parser.add_argument(
        "--mission2-promoted-policy-artifact-dir",
        type=Path,
        default=None,
    )
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--json-output", type=Path, default=None)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the promoted successor comparison and print the report."""

    args = build_parser().parse_args(argv)
    comparison = build_exact_guided_heuristic_comparison(
        seed_stop=args.seed_stop,
        mission1_exact_artifact_dir=args.mission1_exact_artifact_dir,
        mission1_historical_policy_artifact_dir=(
            args.mission1_historical_policy_artifact_dir
        ),
        mission1_promoted_policy_artifact_dir=args.mission1_promoted_policy_artifact_dir,
        mission2_exact_artifact_dir=args.mission2_exact_artifact_dir,
        mission2_historical_policy_artifact_dir=(
            args.mission2_historical_policy_artifact_dir
        ),
        mission2_promoted_policy_artifact_dir=args.mission2_promoted_policy_artifact_dir,
    )
    report = format_exact_guided_heuristic_report(comparison)
    print(report)

    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(f"{report}\n", encoding="utf-8")

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(
            json.dumps(comparison.to_payload(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
