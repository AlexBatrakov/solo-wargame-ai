"""Thin operator surface for the aggregate accepted Phase 5 results."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from solo_wargame_ai.eval.learned_policy_summary import (
    build_phase5_aggregate_summary,
    format_phase5_aggregate_summary,
    phase5_aggregate_summary_payload,
)


def build_parser() -> argparse.ArgumentParser:
    """Build the narrow aggregate Phase 5 summary CLI."""

    parser = argparse.ArgumentParser(
        description="Summarize the accepted Phase 5 training-seed results.",
    )
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        action="append",
        required=True,
        help="One Phase 5 artifact directory containing training/eval outputs.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optionally write the plain-text summary to a file.",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        help="Optionally write the machine-readable summary payload to a JSON file.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Load the accepted training-seed artifacts and print the aggregate summary."""

    args = build_parser().parse_args(argv)
    summary = build_phase5_aggregate_summary(tuple(args.artifact_dir))
    report = format_phase5_aggregate_summary(summary)
    print(report)

    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(f"{report}\n", encoding="utf-8")

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(
            json.dumps(phase5_aggregate_summary_payload(summary), indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
