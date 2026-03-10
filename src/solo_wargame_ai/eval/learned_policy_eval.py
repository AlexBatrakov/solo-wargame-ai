"""Learned-policy evaluation helpers over the accepted Phase 4 env surface."""

from __future__ import annotations

from collections.abc import Sequence
from contextlib import nullcontext
from dataclasses import dataclass

from solo_wargame_ai.agents.learned_policy import (
    LearnedPolicy,
    LearnedPolicyFactory,
    legal_action_ids_from_info,
    policy_name,
)
from solo_wargame_ai.domain.mission import Mission
from solo_wargame_ai.domain.state import TerminalOutcome
from solo_wargame_ai.env import Mission1Env
from solo_wargame_ai.env.mission1_env import EnvInfo
from solo_wargame_ai.env.observation import Observation
from solo_wargame_ai.eval.episode_runner import EpisodeResult
from solo_wargame_ai.eval.metrics import EpisodeMetrics, aggregate_episode_results

from .phase5_seed_policy import PHASE5_BENCHMARK_EVAL_SEEDS, PHASE5_SMOKE_EVAL_SEEDS

try:
    import torch
except ModuleNotFoundError:  # pragma: no cover - exercised only without torch installed.
    torch = None


@dataclass(frozen=True, slots=True)
class LearnedEpisodeRun:
    """Full one-episode learned-policy output on the accepted env boundary."""

    final_observation: Observation
    final_info: EnvInfo
    result: EpisodeResult


@dataclass(frozen=True, slots=True)
class LearnedPolicyEvaluation:
    """Fixed-seed learned-policy evaluation with the accepted Phase 3 metrics."""

    policy_name: str
    seeds: tuple[int, ...]
    episode_runs: tuple[LearnedEpisodeRun, ...]
    metrics: EpisodeMetrics


def run_learned_episode(
    mission: Mission,
    policy: LearnedPolicy,
    *,
    seed: int,
    evaluation: bool = True,
) -> LearnedEpisodeRun:
    """Run one full Mission 1 episode through ``Mission1Env`` and a learned policy."""

    env = Mission1Env(mission)
    observation, info = env.reset(seed=seed)
    initial_marker_count = len(observation["unresolved_markers"])
    policy.reset()

    terminated = False
    truncated = False

    with _torch_eval_context():
        while not (terminated or truncated):
            legal_action_ids = legal_action_ids_from_info(info)
            if not legal_action_ids:
                raise RuntimeError(
                    "Learned-policy evaluation reached a nonterminal state without legal actions",
                )

            action_id = policy.select_action(
                observation,
                info,
                evaluation=evaluation,
            )
            if action_id not in legal_action_ids:
                raise ValueError(
                    f"Policy {policy_name(policy)!r} returned an illegal action id: {action_id}",
                )

            observation, _, terminated, truncated, info = env.step(action_id)

    if truncated:
        raise RuntimeError(
            "Learned-policy evaluation does not accept truncated episodes in default mode",
        )

    terminal_outcome_name = observation["terminal_outcome"]
    if terminal_outcome_name is None:
        raise RuntimeError("Learned-policy evaluation finished without a terminal outcome")

    return LearnedEpisodeRun(
        final_observation=observation,
        final_info=info,
        result=EpisodeResult(
            agent_name=policy_name(policy),
            seed=seed,
            terminal_outcome=TerminalOutcome(terminal_outcome_name),
            terminal_turn=int(observation["turn"]),
            resolved_marker_count=initial_marker_count - len(observation["unresolved_markers"]),
            removed_german_count=sum(
                1
                for german_unit in observation["revealed_german_units"]
                if german_unit["status"] == "removed"
            ),
            player_decision_count=int(info["decision_step_count"]),
        ),
    )


def run_learned_episodes(
    mission: Mission,
    *,
    policy_factory: LearnedPolicyFactory,
    seeds: Sequence[int],
    evaluation: bool = True,
) -> tuple[LearnedEpisodeRun, ...]:
    """Run one fixed env-seed set with a fresh learned policy instance per episode."""

    return tuple(
        run_learned_episode(
            mission,
            policy_factory(),
            seed=seed,
            evaluation=evaluation,
        )
        for seed in seeds
    )


def evaluate_learned_policy(
    mission: Mission,
    *,
    policy_factory: LearnedPolicyFactory,
    seeds: Sequence[int],
    evaluation: bool = True,
) -> LearnedPolicyEvaluation:
    """Aggregate learned-policy episode runs into the accepted Phase 3 metric schema."""

    episode_runs = run_learned_episodes(
        mission,
        policy_factory=policy_factory,
        seeds=seeds,
        evaluation=evaluation,
    )
    metrics = aggregate_episode_results(run.result for run in episode_runs)
    return LearnedPolicyEvaluation(
        policy_name=metrics.agent_name,
        seeds=tuple(seeds),
        episode_runs=episode_runs,
        metrics=metrics,
    )


def evaluate_phase5_smoke_policy(
    mission: Mission,
    *,
    policy_factory: LearnedPolicyFactory,
    evaluation: bool = True,
) -> LearnedPolicyEvaluation:
    """Run the accepted 16-seed smoke evaluation for a learned policy."""

    return evaluate_learned_policy(
        mission,
        policy_factory=policy_factory,
        seeds=PHASE5_SMOKE_EVAL_SEEDS,
        evaluation=evaluation,
    )


def evaluate_phase5_benchmark_policy(
    mission: Mission,
    *,
    policy_factory: LearnedPolicyFactory,
    evaluation: bool = True,
) -> LearnedPolicyEvaluation:
    """Run the accepted 200-seed benchmark evaluation for a learned policy."""

    return evaluate_learned_policy(
        mission,
        policy_factory=policy_factory,
        seeds=PHASE5_BENCHMARK_EVAL_SEEDS,
        evaluation=evaluation,
    )


__all__ = [
    "LearnedEpisodeRun",
    "LearnedPolicyEvaluation",
    "evaluate_learned_policy",
    "evaluate_phase5_benchmark_policy",
    "evaluate_phase5_smoke_policy",
    "run_learned_episode",
    "run_learned_episodes",
]


def _torch_eval_context():
    if torch is None:
        return nullcontext()
    return torch.inference_mode()
