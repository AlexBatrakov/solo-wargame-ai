"""Thin operator surface for one bounded Phase 5 training run."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from solo_wargame_ai.agents.masked_actor_critic_training import (
    Phase5TrainingConfig,
    default_phase5_output_dir,
    format_phase5_training_report,
    train_masked_actor_critic,
)
from solo_wargame_ai.io.mission_loader import load_mission

MISSION_PATH = (
    Path(__file__).resolve().parents[3]
    / "configs"
    / "missions"
    / "mission_01_secure_the_woods_1.toml"
)


def build_parser() -> argparse.ArgumentParser:
    """Build the narrow Phase 5 train-smoke / train-run CLI surface."""

    parser = argparse.ArgumentParser(
        description=(
            "Run one bounded Phase 5 masked actor-critic training pass on Mission 1."
        ),
    )
    parser.add_argument(
        "--training-seed",
        type=int,
        required=True,
        help="One accepted Phase 5 training seed.",
    )
    parser.add_argument(
        "--episodes",
        type=int,
        required=True,
        help="Total number of training episodes to run.",
    )
    parser.add_argument(
        "--checkpoint-interval",
        type=int,
        required=True,
        help="Save and score one checkpoint every N episodes.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help=(
            "Optional artifact directory. Defaults to "
            "outputs/phase5/train_seed_<seed>_ep_<episodes>."
        ),
    )
    parser.add_argument(
        "--overwrite-output-dir",
        action="store_true",
        help="Explicitly replace a non-empty artifact directory.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run one bounded Phase 5 training pass and print the saved summary."""

    args = build_parser().parse_args(argv)
    mission = load_mission(MISSION_PATH)
    config = Phase5TrainingConfig(
        training_seed=args.training_seed,
        total_episodes=args.episodes,
        checkpoint_interval=args.checkpoint_interval,
    )
    output_dir = (
        default_phase5_output_dir(config)
        if args.output_dir is None
        else args.output_dir
    )
    training_run = train_masked_actor_critic(
        mission,
        config=config,
        output_dir=output_dir,
        overwrite_output_dir=args.overwrite_output_dir,
    )
    print(format_phase5_training_report(training_run))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
