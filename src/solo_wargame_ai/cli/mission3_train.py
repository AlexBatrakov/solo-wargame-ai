"""Thin operator surface for one bounded Mission 3 learned-policy training run."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from solo_wargame_ai.agents.masked_actor_critic_training import (
    Phase5TrainingConfig,
    train_masked_actor_critic,
)
from solo_wargame_ai.eval.mission3_learned_policy_reporting import (
    format_mission3_training_report,
)
from solo_wargame_ai.eval.mission3_learned_policy_seeds import (
    MISSION3_LEARNING_FEATURE_ADAPTER_SEED,
    MISSION3_LEARNING_MODEL_SELECTION_SEEDS,
    MISSION3_LEARNING_TRAINING_SEEDS,
)
from solo_wargame_ai.io.mission_loader import load_mission

MISSION_PATH = (
    Path(__file__).resolve().parents[3]
    / "configs"
    / "missions"
    / "mission_03_secure_the_building.toml"
)
DEFAULT_MISSION3_OUTPUT_ROOT = Path("outputs") / "mission3_learning"


def build_parser() -> argparse.ArgumentParser:
    """Build the narrow Mission 3 training CLI surface."""

    parser = argparse.ArgumentParser(
        description=(
            "Run one bounded masked actor-critic training pass on Mission 3."
        ),
    )
    parser.add_argument(
        "--training-seed",
        type=int,
        required=True,
        help="One accepted Mission 3 learned-policy training seed.",
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
            "outputs/mission3_learning/train_seed_<seed>_ep_<episodes>."
        ),
    )
    parser.add_argument(
        "--overwrite-output-dir",
        action="store_true",
        help="Explicitly replace a non-empty artifact directory.",
    )
    return parser


def default_mission3_output_dir(
    *,
    training_seed: int,
    total_episodes: int,
    output_root: Path = DEFAULT_MISSION3_OUTPUT_ROOT,
) -> Path:
    """Return the default Mission 3 artifact directory for one training run."""

    return output_root / f"train_seed_{training_seed}_ep_{total_episodes}"


def main(argv: Sequence[str] | None = None) -> int:
    """Run one bounded Mission 3 training pass and print the saved report."""

    args = build_parser().parse_args(argv)
    if args.training_seed not in MISSION3_LEARNING_TRAINING_SEEDS:
        raise ValueError(
            "Mission 3 training seed must be one of the accepted seeds "
            f"{MISSION3_LEARNING_TRAINING_SEEDS!r}",
        )

    mission = load_mission(MISSION_PATH)
    config = Phase5TrainingConfig(
        training_seed=args.training_seed,
        total_episodes=args.episodes,
        checkpoint_interval=args.checkpoint_interval,
        feature_adapter_seed=MISSION3_LEARNING_FEATURE_ADAPTER_SEED,
        model_selection_seeds=MISSION3_LEARNING_MODEL_SELECTION_SEEDS,
    )
    output_dir = (
        default_mission3_output_dir(
            training_seed=args.training_seed,
            total_episodes=args.episodes,
        )
        if args.output_dir is None
        else args.output_dir
    )
    training_run = train_masked_actor_critic(
        mission,
        config=config,
        output_dir=output_dir,
        overwrite_output_dir=args.overwrite_output_dir,
    )
    report = format_mission3_training_report(
        training_run,
        artifact_root=DEFAULT_MISSION3_OUTPUT_ROOT,
    )
    training_run.report_path.write_text(f"{report}\n", encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
