from __future__ import annotations

import json

import pytest

from solo_wargame_ai.eval.metrics import EpisodeMetrics
from solo_wargame_ai.eval.mission3_learned_policy_reporting import (
    MISSION3_HISTORICAL_REFERENCE_QUALIFICATION,
    Mission3EvalCheckpointMetadata,
    build_mission3_historical_comparison,
    format_mission3_eval_report,
)
from solo_wargame_ai.eval.mission3_learned_policy_seeds import (
    MISSION3_LEARNING_BENCHMARK_EVAL_SEEDS,
    MISSION3_LEARNING_FEATURE_ADAPTER_SEED,
    MISSION3_LEARNING_MODEL_SELECTION_SEEDS,
    MISSION3_LEARNING_SMOKE_EVAL_SEEDS,
    MISSION3_LEARNING_TRAINING_SEEDS,
    mission3_training_rollout_seed,
)
from solo_wargame_ai.eval.mission3_learned_policy_summary import (
    build_mission3_aggregate_summary,
)


def _metrics(
    *,
    wins: int,
    episodes: int,
    agent_name: str = "masked_actor_critic",
) -> EpisodeMetrics:
    return EpisodeMetrics(
        agent_name=agent_name,
        episode_count=episodes,
        victory_count=wins,
        defeat_count=episodes - wins,
        win_rate=wins / episodes,
        defeat_rate=(episodes - wins) / episodes,
        mean_terminal_turn=4.0,
        mean_resolved_marker_count=1.0,
        mean_removed_german_count=0.5,
        mean_player_decision_count=10.0,
    )


def test_mission3_seed_aliases_track_the_fixed_local_ranges() -> None:
    rollout_seeds = {
        mission3_training_rollout_seed(training_seed, episode_index)
        for training_seed in MISSION3_LEARNING_TRAINING_SEEDS
        for episode_index in range(3)
    }

    assert MISSION3_LEARNING_TRAINING_SEEDS == (101, 202, 303)
    assert MISSION3_LEARNING_FEATURE_ADAPTER_SEED == 4_000
    assert MISSION3_LEARNING_MODEL_SELECTION_SEEDS == tuple(range(2_000, 2_016))
    assert MISSION3_LEARNING_SMOKE_EVAL_SEEDS == tuple(range(16))
    assert MISSION3_LEARNING_BENCHMARK_EVAL_SEEDS == tuple(range(200))
    assert rollout_seeds.isdisjoint(MISSION3_LEARNING_SMOKE_EVAL_SEEDS)
    assert rollout_seeds.isdisjoint(MISSION3_LEARNING_BENCHMARK_EVAL_SEEDS)
    assert rollout_seeds.isdisjoint(MISSION3_LEARNING_MODEL_SELECTION_SEEDS)


def test_mission3_eval_report_marks_historical_refs_as_oracle_style() -> None:
    comparison = build_mission3_historical_comparison(
        mode="benchmark",
        metrics=_metrics(wins=60, episodes=200),
    )
    report = format_mission3_eval_report(
        mode="benchmark",
        checkpoint_path="outputs/mission3_learning/example.pt",
        metrics=_metrics(wins=60, episodes=200),
        seeds=MISSION3_LEARNING_BENCHMARK_EVAL_SEEDS,
        checkpoint_metadata=Mission3EvalCheckpointMetadata(
            training_seed=101,
            checkpoint_episode=1750,
            checkpoint_step=43101,
            model_selection_seeds=MISSION3_LEARNING_MODEL_SELECTION_SEEDS,
            checkpoint_selection_policy="best greedy masked win count",
        ),
    )

    assert comparison.random_reference_wins == 0
    assert comparison.heuristic_reference_wins == 72
    assert comparison.rollout_search_reference_wins == 105
    assert comparison.wins_vs_random == 60
    assert comparison.wins_vs_heuristic_reference == -12
    assert comparison.wins_vs_rollout_search_reference == -45
    assert MISSION3_HISTORICAL_REFERENCE_QUALIFICATION in report
    assert "heuristic_wins: 72" in report
    assert "rollout_search_wins: 105" in report
    assert "wins_vs_rollout_search_reference: -45" in report


def test_mission3_aggregate_summary_rejects_mixed_eval_modes(tmp_path) -> None:
    smoke_dir = tmp_path / "smoke"
    smoke_dir.mkdir()
    (smoke_dir / "training_summary.json").write_text(
        json.dumps(
            {
                "training_seed": 101,
                "selected_checkpoint_path": "outputs/mission3_learning/smoke.pt",
            },
        )
        + "\n",
        encoding="utf-8",
    )
    (smoke_dir / "smoke_eval.json").write_text(
        json.dumps(
            {
                "metrics": {
                    "agent_name": "masked_actor_critic",
                    "episode_count": 16,
                    "victory_count": 4,
                    "defeat_count": 12,
                    "win_rate": 0.25,
                    "defeat_rate": 0.75,
                    "mean_terminal_turn": 4.0,
                    "mean_resolved_marker_count": 1.0,
                    "mean_removed_german_count": 0.5,
                    "mean_player_decision_count": 10.0,
                },
            },
        )
        + "\n",
        encoding="utf-8",
    )

    benchmark_dir = tmp_path / "benchmark"
    benchmark_dir.mkdir()
    (benchmark_dir / "training_summary.json").write_text(
        json.dumps(
            {
                "training_seed": 202,
                "selected_checkpoint_path": "outputs/mission3_learning/benchmark.pt",
            },
        )
        + "\n",
        encoding="utf-8",
    )
    (benchmark_dir / "benchmark_eval.json").write_text(
        json.dumps(
            {
                "metrics": {
                    "agent_name": "masked_actor_critic",
                    "episode_count": 200,
                    "victory_count": 40,
                    "defeat_count": 160,
                    "win_rate": 0.2,
                    "defeat_rate": 0.8,
                    "mean_terminal_turn": 4.0,
                    "mean_resolved_marker_count": 1.0,
                    "mean_removed_german_count": 0.5,
                    "mean_player_decision_count": 10.0,
                },
            },
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="one shared evaluation mode"):
        build_mission3_aggregate_summary((smoke_dir, benchmark_dir))
