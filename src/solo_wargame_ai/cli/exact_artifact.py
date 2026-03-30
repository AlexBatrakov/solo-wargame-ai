"""Thin CLI for the generic exact-artifact workflow."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from solo_wargame_ai.eval.exact_artifact import (
    build_exact_artifact,
    default_exact_artifact_dir,
    read_exact_artifact_stats,
    verify_exact_artifact,
)


def build_parser() -> argparse.ArgumentParser:
    """Build the generic exact-artifact CLI parser."""

    parser = argparse.ArgumentParser(
        description="Generic exact-artifact build/read/verify workflow.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build", help="Build an exact artifact.")
    build_parser.add_argument("--mission", type=Path, required=True, help="Mission TOML path.")
    build_parser.add_argument(
        "--artifact-dir",
        type=Path,
        help=(
            "Optional output directory. "
            "Default: .project_local/artifacts/<mission_id>_exact_artifact"
        ),
    )
    build_parser.add_argument("--progress-interval-sec", type=float, default=30.0)
    build_parser.add_argument("--insert-batch-size", type=int, default=20_000)
    build_parser.add_argument("--cap-metric", choices=("auto", "rss", "footprint"), default="auto")
    build_parser.add_argument("--memory-cap-gb", type=float, default=20.0)
    build_parser.add_argument("--memory-low-water-gb", type=float, default=17.0)
    build_parser.add_argument("--trim-check-interval", type=int, default=2048)
    build_parser.add_argument("--min-trim-entries", type=int, default=8192)
    build_parser.add_argument("--cache-through-turn", type=int, default=None)
    build_parser.add_argument("--overwrite", action="store_true")
    build_parser.add_argument("--store-action-values", action="store_true")
    build_parser.add_argument("--exact-tie-tolerance", type=float, default=1e-15)

    stats_parser = subparsers.add_parser("stats", help="Print exact-artifact metadata.")
    stats_parser.add_argument("--artifact-dir", type=Path, required=True)

    verify_parser = subparsers.add_parser("verify", help="Verify artifact root lookup.")
    verify_parser.add_argument("--artifact-dir", type=Path, required=True)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the generic exact-artifact CLI."""

    args = build_parser().parse_args(argv)

    if args.command == "build":
        artifact_dir = args.artifact_dir or default_exact_artifact_dir(args.mission)
        payload = build_exact_artifact(
            mission_path=args.mission,
            artifact_dir=artifact_dir,
            progress_interval_sec=args.progress_interval_sec,
            insert_batch_size=args.insert_batch_size,
            cap_metric=args.cap_metric,
            memory_cap_gb=args.memory_cap_gb,
            memory_low_water_gb=args.memory_low_water_gb,
            trim_check_interval=args.trim_check_interval,
            min_trim_entries=args.min_trim_entries,
            cache_through_turn=args.cache_through_turn,
            overwrite=args.overwrite,
            store_action_values=args.store_action_values,
            exact_tie_tolerance=args.exact_tie_tolerance,
        )
    elif args.command == "stats":
        payload = read_exact_artifact_stats(args.artifact_dir)
    else:
        payload = verify_exact_artifact(args.artifact_dir).to_payload()

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
