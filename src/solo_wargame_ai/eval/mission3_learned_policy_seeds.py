"""Mission-3-local seed aliases for the first learned-policy surface."""

from __future__ import annotations

from solo_wargame_ai.eval.learned_policy_seeds import training_rollout_seed
from solo_wargame_ai.eval.mission3_comparison import (
    MISSION3_BENCHMARK_SEEDS,
    MISSION3_SMOKE_SEEDS,
)

MISSION3_LEARNING_FEATURE_ADAPTER_SEED = 4_000
MISSION3_LEARNING_TRAINING_SEEDS: tuple[int, ...] = (101, 202, 303)
MISSION3_LEARNING_MODEL_SELECTION_SEEDS: tuple[int, ...] = tuple(range(2_000, 2_016))
MISSION3_LEARNING_SMOKE_EVAL_SEEDS: tuple[int, ...] = MISSION3_SMOKE_SEEDS
MISSION3_LEARNING_BENCHMARK_EVAL_SEEDS: tuple[int, ...] = MISSION3_BENCHMARK_SEEDS


def mission3_training_rollout_seed(training_seed: int, episode_index: int) -> int:
    """Derive rollout-only Mission 3 training seeds with the accepted policy."""

    return training_rollout_seed(training_seed, episode_index)


__all__ = [
    "MISSION3_LEARNING_BENCHMARK_EVAL_SEEDS",
    "MISSION3_LEARNING_FEATURE_ADAPTER_SEED",
    "MISSION3_LEARNING_MODEL_SELECTION_SEEDS",
    "MISSION3_LEARNING_SMOKE_EVAL_SEEDS",
    "MISSION3_LEARNING_TRAINING_SEEDS",
    "mission3_training_rollout_seed",
]
