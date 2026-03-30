"""Thin CLI for the generic exact-backed mission-summary workflow."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from solo_wargame_ai.eval.agent_loader import (
    ExplicitAgentLoaderSpec,
    build_explicit_agent_factory,
    resolve_explicit_agent_name,
    validate_agent_loader_spec,
)
from solo_wargame_ai.eval.mission_summary import (
    build_mission_summary,
    format_mission_summary_report,
)


def build_parser() -> argparse.ArgumentParser:
    """Build the generic mission-summary CLI parser."""

    parser = argparse.ArgumentParser(
        description="Generic exact-backed mission summary for an exact-solved mission.",
    )
    parser.add_argument("--mission", type=Path, required=True, help="Mission TOML path.")
    parser.add_argument("--exact-artifact-dir", type=Path, default=None)
    parser.add_argument("--policy-artifact-dir", type=Path, default=None)
    agent_group = parser.add_mutually_exclusive_group()
    agent_group.add_argument(
        "--agent-factory",
        help="Import path in the form module:function returning an initialized agent.",
    )
    agent_group.add_argument(
        "--agent-module",
        help="Module used together with --agent-expr.",
    )
    parser.add_argument("--agent-expr", default=None)
    parser.add_argument("--agent-name", default=None)
    parser.add_argument("--seed-stop", type=int, default=200)
    parser.add_argument("--allow-full-solver-replay", action="store_true")
    parser.add_argument("--disable-known-anchor", action="store_true")
    parser.add_argument("--progress-interval-sec", type=float, default=30.0)
    parser.add_argument("--cap-metric", choices=("auto", "rss", "footprint"), default="auto")
    parser.add_argument("--memory-cap-gb", type=float, default=20.0)
    parser.add_argument("--memory-low-water-gb", type=float, default=17.0)
    parser.add_argument("--trim-check-interval", type=int, default=2048)
    parser.add_argument("--min-trim-entries", type=int, default=8192)
    parser.add_argument("--cache-through-turn", type=int, default=None)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--json-output", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the generic mission-summary CLI."""

    args = build_parser().parse_args(argv)

    build_agent = None
    agent_name = args.agent_name
    has_loader_args = (
        args.agent_factory is not None
        or args.agent_module is not None
        or args.agent_expr is not None
    )
    if has_loader_args:
        spec = ExplicitAgentLoaderSpec(
            agent_factory=args.agent_factory,
            agent_module=args.agent_module,
            agent_expr=args.agent_expr,
            agent_name=args.agent_name,
        )
        validate_agent_loader_spec(spec, require_loader=True)
        build_agent = build_explicit_agent_factory(spec)
        agent_name = resolve_explicit_agent_name(spec, agent_factory=build_agent)

    summary = build_mission_summary(
        mission_path=args.mission,
        exact_artifact_dir=args.exact_artifact_dir,
        policy_artifact_dir=args.policy_artifact_dir,
        build_agent=build_agent,
        agent_name=agent_name,
        seed_stop=args.seed_stop,
        allow_known_anchor=not args.disable_known_anchor,
        allow_full_solver_replay=args.allow_full_solver_replay,
        progress_interval_sec=args.progress_interval_sec,
        cap_metric=args.cap_metric,
        memory_cap_gb=args.memory_cap_gb,
        memory_low_water_gb=args.memory_low_water_gb,
        trim_check_interval=args.trim_check_interval,
        min_trim_entries=args.min_trim_entries,
        cache_through_turn=args.cache_through_turn,
    )
    report = format_mission_summary_report(summary)
    print(report)

    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(f"{report}\n", encoding="utf-8")

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(
            json.dumps(summary.to_payload(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
