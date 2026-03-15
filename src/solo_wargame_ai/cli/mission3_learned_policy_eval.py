"""Thin operator surface for Mission 3 learned-policy evaluation."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from solo_wargame_ai.agents.masked_actor_critic import MaskedActorCriticPolicy
from solo_wargame_ai.agents.masked_actor_critic_training import load_phase5_checkpoint
from solo_wargame_ai.eval.learned_policy_eval import evaluate_learned_policy
from solo_wargame_ai.eval.mission3_learned_policy_reporting import (
    Mission3EvalCheckpointMetadata,
    format_mission3_eval_report,
    mission3_eval_payload,
)
from solo_wargame_ai.eval.mission3_learned_policy_seeds import (
    MISSION3_LEARNING_BENCHMARK_EVAL_SEEDS,
    MISSION3_LEARNING_SMOKE_EVAL_SEEDS,
)
from solo_wargame_ai.io.mission_loader import load_mission

MISSION_PATH = (
    Path(__file__).resolve().parents[3]
    / "configs"
    / "missions"
    / "mission_03_secure_the_building.toml"
)


def build_parser() -> argparse.ArgumentParser:
    """Build the Mission 3 learned-policy evaluation CLI."""

    parser = argparse.ArgumentParser(
        description="Evaluate one saved Mission 3 learned-policy checkpoint.",
    )
    parser.add_argument(
        "--checkpoint",
        type=Path,
        required=True,
        help="Path to the selected Mission 3 checkpoint file.",
    )
    parser.add_argument(
        "--mode",
        choices=("smoke", "benchmark"),
        required=True,
        help="Run the Mission 3 smoke or benchmark seed surface.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optionally write the plain-text report to a file.",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        help="Optionally write the machine-readable evaluation payload to JSON.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the requested Mission 3 learned-policy evaluation."""

    args = build_parser().parse_args(argv)
    mission = load_mission(MISSION_PATH)
    loaded_checkpoint = load_phase5_checkpoint(mission, args.checkpoint)

    def policy_factory() -> MaskedActorCriticPolicy:
        return MaskedActorCriticPolicy(
            loaded_checkpoint.adapter,
            loaded_checkpoint.model,
            seed=loaded_checkpoint.training_seed,
        )

    seeds = (
        MISSION3_LEARNING_SMOKE_EVAL_SEEDS
        if args.mode == "smoke"
        else MISSION3_LEARNING_BENCHMARK_EVAL_SEEDS
    )
    evaluation = evaluate_learned_policy(
        mission,
        policy_factory=policy_factory,
        seeds=seeds,
        evaluation=True,
    )

    checkpoint_metadata = Mission3EvalCheckpointMetadata(
        training_seed=loaded_checkpoint.training_seed,
        checkpoint_episode=loaded_checkpoint.checkpoint_episode,
        checkpoint_step=loaded_checkpoint.checkpoint_step,
        model_selection_seeds=loaded_checkpoint.model_selection_seeds,
        checkpoint_selection_policy=loaded_checkpoint.checkpoint_selection_policy,
    )
    report = format_mission3_eval_report(
        mode=args.mode,
        checkpoint_path=str(args.checkpoint),
        metrics=evaluation.metrics,
        seeds=evaluation.seeds,
        checkpoint_metadata=checkpoint_metadata,
    )
    print(report)

    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(f"{report}\n", encoding="utf-8")

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(
            json.dumps(
                mission3_eval_payload(
                    mode=args.mode,
                    checkpoint_path=str(args.checkpoint),
                    metrics=evaluation.metrics,
                    seeds=evaluation.seeds,
                    checkpoint_metadata=checkpoint_metadata,
                ),
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
