from __future__ import annotations

from pathlib import Path

from solo_wargame_ai.domain.state import TerminalOutcome
from solo_wargame_ai.eval.learned_policy_eval import evaluate_learned_policy
from solo_wargame_ai.eval.learned_policy_seeds import (
    PHASE5_BENCHMARK_EVAL_SEEDS,
    PHASE5_FEATURE_ADAPTER_SEED,
    PHASE5_MODEL_SELECTION_SEEDS,
    PHASE5_SMOKE_EVAL_SEEDS,
    PHASE5_TRAINING_SEEDS,
    training_rollout_seed,
)
from solo_wargame_ai.eval.metrics import aggregate_episode_results
from solo_wargame_ai.io.mission_loader import load_mission

MISSION_PATH = (
    Path(__file__).resolve().parents[2]
    / "configs"
    / "missions"
    / "mission_01_secure_the_woods_1.toml"
)


class FirstLegalPolicy:
    name = "first_legal"

    def reset(self) -> None:
        return None

    def select_action(
        self,
        observation: object,
        info: dict[str, object],
        *,
        evaluation: bool,
    ) -> int:
        del observation, evaluation
        return int(info["legal_action_ids"][0])


def test_learned_policy_evaluation_reuses_the_phase3_metric_schema() -> None:
    mission = load_mission(MISSION_PATH)

    evaluation = evaluate_learned_policy(
        mission,
        policy_factory=FirstLegalPolicy,
        seeds=(0, 1),
        evaluation=True,
    )

    manual_metrics = aggregate_episode_results(run.result for run in evaluation.episode_runs)

    assert evaluation.metrics == manual_metrics
    assert evaluation.policy_name == "first_legal"
    assert evaluation.metrics.agent_name == "first_legal"
    assert evaluation.metrics.episode_count == 2
    assert tuple(run.result.seed for run in evaluation.episode_runs) == (0, 1)
    assert all(run.result.terminal_outcome in TerminalOutcome for run in evaluation.episode_runs)
    assert all(
        run.result.player_decision_count == run.final_info["decision_step_count"]
        for run in evaluation.episode_runs
    )


def test_training_rollout_seed_policy_stays_separate_from_eval_seed_sets() -> None:
    rollout_seeds = {
        training_rollout_seed(training_seed, episode_index)
        for training_seed in PHASE5_TRAINING_SEEDS
        for episode_index in range(3)
    }

    assert rollout_seeds.isdisjoint(PHASE5_SMOKE_EVAL_SEEDS)
    assert rollout_seeds.isdisjoint(PHASE5_BENCHMARK_EVAL_SEEDS)
    assert rollout_seeds.isdisjoint(PHASE5_MODEL_SELECTION_SEEDS)


def test_phase5_seed_policy_constants_are_frozen_to_the_accepted_ranges() -> None:
    assert PHASE5_TRAINING_SEEDS == (101, 202, 303)
    assert PHASE5_FEATURE_ADAPTER_SEED == 4_000
    assert PHASE5_MODEL_SELECTION_SEEDS == tuple(range(2_000, 2_016))
    assert PHASE5_SMOKE_EVAL_SEEDS == tuple(range(16))
    assert PHASE5_BENCHMARK_EVAL_SEEDS == tuple(range(200))
