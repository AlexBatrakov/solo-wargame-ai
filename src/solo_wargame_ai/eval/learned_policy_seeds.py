"""Explicit seed-policy separation for the first learned-policy stack."""

from __future__ import annotations

from solo_wargame_ai.eval.benchmark import PHASE3_BENCHMARK_SEEDS
from solo_wargame_ai.eval.episode_runner import PHASE3_SMOKE_SEEDS

PHASE5_FEATURE_ADAPTER_SEED = 4_000
PHASE5_TRAINING_SEEDS: tuple[int, ...] = (101, 202, 303)
PHASE5_MODEL_SELECTION_SEEDS: tuple[int, ...] = tuple(range(2_000, 2_016))
PHASE5_SMOKE_EVAL_SEEDS: tuple[int, ...] = PHASE3_SMOKE_SEEDS
PHASE5_BENCHMARK_EVAL_SEEDS: tuple[int, ...] = PHASE3_BENCHMARK_SEEDS
_TRAINING_ROLLOUT_SEED_OFFSET = 10_000
_TRAINING_ROLLOUT_SEED_STRIDE = 100_000


def training_rollout_seed(training_seed: int, episode_index: int) -> int:
    """Derive rollout-only training seeds that stay separate from eval seeds."""

    if training_seed < 0:
        raise ValueError("training_seed must be non-negative")
    if episode_index < 0:
        raise ValueError("episode_index must be non-negative")
    return (
        _TRAINING_ROLLOUT_SEED_OFFSET
        + (training_seed * _TRAINING_ROLLOUT_SEED_STRIDE)
        + episode_index
    )


__all__ = [
    "PHASE5_BENCHMARK_EVAL_SEEDS",
    "PHASE5_FEATURE_ADAPTER_SEED",
    "PHASE5_MODEL_SELECTION_SEEDS",
    "PHASE5_SMOKE_EVAL_SEEDS",
    "PHASE5_TRAINING_SEEDS",
    "training_rollout_seed",
]
