"""Thin operator surface for Mission 3 learned-policy artifact summaries."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from solo_wargame_ai.eval.mission3_learned_policy_summary import (
    build_mission3_aggregate_summary,
    format_mission3_aggregate_summary,
    mission3_aggregate_summary_payload,
)


def build_parser() -> argparse.ArgumentParser:
    """Build the Mission 3 learned-policy summary CLI."""

    parser = argparse.ArgumentParser(
        description="Summarize Mission 3 learned-policy artifact directories.",
    )
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        action="append",
        required=True,
        help="One Mission 3 artifact directory containing training/eval outputs.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optionally write the plain-text summary to a file.",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        help="Optionally write the machine-readable summary payload to JSON.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Load Mission 3 artifact dirs and print the aggregate summary."""

    args = build_parser().parse_args(argv)
    summary = build_mission3_aggregate_summary(tuple(args.artifact_dir))
    report = format_mission3_aggregate_summary(summary)
    print(report)

    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(f"{report}\n", encoding="utf-8")

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(
            json.dumps(
                mission3_aggregate_summary_payload(summary),
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
