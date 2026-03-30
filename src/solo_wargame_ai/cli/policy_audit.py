"""Thin CLI for the generic policy-audit workflow."""

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
from solo_wargame_ai.eval.policy_audit import (
    build_policy_audit_artifact,
    default_policy_audit_dir,
    read_policy_audit_stats,
    verify_policy_audit_artifact,
)


def build_parser() -> argparse.ArgumentParser:
    """Build the generic policy-audit CLI parser."""

    parser = argparse.ArgumentParser(
        description="Generic fixed-policy audit artifact workflow.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build", help="Build a policy-audit artifact.")
    build_parser.add_argument("--mission", type=Path, required=True, help="Mission TOML path.")
    agent_group = build_parser.add_mutually_exclusive_group(required=True)
    agent_group.add_argument(
        "--agent-factory",
        help="Import path in the form module:function returning an initialized agent.",
    )
    agent_group.add_argument(
        "--agent-module",
        help="Module used together with --agent-expr.",
    )
    build_parser.add_argument("--agent-expr", default=None)
    build_parser.add_argument("--agent-name", default=None)
    build_parser.add_argument("--artifact-dir", type=Path)
    build_parser.add_argument("--exact-artifact-dir", type=Path, default=None)
    build_parser.add_argument("--progress-interval-sec", type=float, default=30.0)
    build_parser.add_argument("--insert-batch-size", type=int, default=50_000)
    build_parser.add_argument("--cap-metric", choices=("auto", "rss", "footprint"), default="auto")
    build_parser.add_argument("--memory-cap-gb", type=float, default=20.0)
    build_parser.add_argument("--memory-low-water-gb", type=float, default=17.0)
    build_parser.add_argument("--trim-check-interval", type=int, default=2048)
    build_parser.add_argument("--min-trim-entries", type=int, default=8192)
    build_parser.add_argument("--cache-through-turn", type=int, default=None)
    build_parser.add_argument("--store-action-values", action="store_true")
    build_parser.add_argument("--exact-tie-tolerance", type=float, default=1e-15)
    build_parser.add_argument("--policy-tie-tolerance", type=float, default=1e-15)
    build_parser.add_argument("--overwrite", action="store_true")

    stats_parser = subparsers.add_parser("stats", help="Print policy-audit metadata.")
    stats_parser.add_argument("--artifact-dir", type=Path, required=True)

    verify_parser = subparsers.add_parser("verify", help="Verify the policy-audit root row.")
    verify_parser.add_argument("--artifact-dir", type=Path, required=True)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the generic policy-audit CLI."""

    args = build_parser().parse_args(argv)

    if args.command == "build":
        spec = ExplicitAgentLoaderSpec(
            agent_factory=args.agent_factory,
            agent_module=args.agent_module,
            agent_expr=args.agent_expr,
            agent_name=args.agent_name,
        )
        validate_agent_loader_spec(spec, require_loader=True)
        build_agent = build_explicit_agent_factory(spec)
        agent_name = resolve_explicit_agent_name(spec, agent_factory=build_agent)
        artifact_dir = args.artifact_dir or default_policy_audit_dir(args.mission, agent_name)
        payload = build_policy_audit_artifact(
            mission_path=args.mission,
            exact_artifact_dir=args.exact_artifact_dir,
            build_agent=build_agent,
            agent_name=agent_name,
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
            policy_tie_tolerance=args.policy_tie_tolerance,
        )
    elif args.command == "stats":
        payload = read_policy_audit_stats(args.artifact_dir)
    else:
        payload = verify_policy_audit_artifact(args.artifact_dir).to_payload()

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
