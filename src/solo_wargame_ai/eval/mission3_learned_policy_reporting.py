"""Mission-3-local reporting helpers for the first learned-policy surface."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from solo_wargame_ai.agents.masked_actor_critic_training import (
    PHASE5_CHECKPOINT_SELECTION_POLICY,
    Phase5TrainingRun,
)
from solo_wargame_ai.eval.metrics import EpisodeMetrics, format_metrics_table

Mission3LearnedPolicyEvalMode = Literal["smoke", "benchmark"]

MISSION3_HISTORICAL_REFERENCE_QUALIFICATION = (
    "Preserved Mission 3 heuristic/search references are oracle-style or "
    "branch-clairvoyant history and are not fair learned-policy targets."
)
MISSION3_OBSERVATION_BASED_SURFACE = (
    "Observation-based learned policy on the accepted Mission3Env contract."
)


@dataclass(frozen=True, slots=True)
class Mission3HistoricalReference:
    """Preserved Mission 3 local reference wins for one evaluation mode."""

    mode: Mission3LearnedPolicyEvalMode
    episode_count: int
    random_wins: int
    heuristic_wins: int
    rollout_search_wins: int


@dataclass(frozen=True, slots=True)
class Mission3HistoricalComparison:
    """Descriptive learned-policy win deltas versus preserved history."""

    mode: Mission3LearnedPolicyEvalMode
    episode_count: int
    random_reference_wins: int
    heuristic_reference_wins: int
    rollout_search_reference_wins: int
    wins_vs_random: int
    wins_vs_heuristic_reference: int
    wins_vs_rollout_search_reference: int


@dataclass(frozen=True, slots=True)
class Mission3EvalCheckpointMetadata:
    """Checkpoint metadata surfaced into Mission 3 learned-policy reports."""

    training_seed: int
    checkpoint_episode: int
    checkpoint_step: int
    model_selection_seeds: tuple[int, ...]
    checkpoint_selection_policy: str


def accepted_mission3_historical_reference(
    mode: Mission3LearnedPolicyEvalMode,
) -> Mission3HistoricalReference:
    """Return the preserved Mission 3 reference wins for one eval mode."""

    if mode == "smoke":
        return Mission3HistoricalReference(
            mode=mode,
            episode_count=16,
            random_wins=0,
            heuristic_wins=7,
            rollout_search_wins=8,
        )
    if mode == "benchmark":
        return Mission3HistoricalReference(
            mode=mode,
            episode_count=200,
            random_wins=0,
            heuristic_wins=72,
            rollout_search_wins=105,
        )
    raise ValueError(f"Unsupported Mission 3 evaluation mode: {mode!r}")


def build_mission3_historical_comparison(
    *,
    mode: Mission3LearnedPolicyEvalMode,
    metrics: EpisodeMetrics,
) -> Mission3HistoricalComparison:
    """Compare one learned-policy result against preserved Mission 3 history."""

    historical_reference = accepted_mission3_historical_reference(mode)
    if metrics.episode_count != historical_reference.episode_count:
        raise ValueError(
            "Mission 3 evaluation metrics do not match the preserved episode count "
            f"for mode {mode!r}: expected {historical_reference.episode_count}, "
            f"got {metrics.episode_count}",
        )
    return Mission3HistoricalComparison(
        mode=mode,
        episode_count=historical_reference.episode_count,
        random_reference_wins=historical_reference.random_wins,
        heuristic_reference_wins=historical_reference.heuristic_wins,
        rollout_search_reference_wins=historical_reference.rollout_search_wins,
        wins_vs_random=metrics.victory_count - historical_reference.random_wins,
        wins_vs_heuristic_reference=(
            metrics.victory_count - historical_reference.heuristic_wins
        ),
        wins_vs_rollout_search_reference=(
            metrics.victory_count - historical_reference.rollout_search_wins
        ),
    )


def format_seed_set(seeds: tuple[int, ...]) -> str:
    """Render one fixed seed tuple in a compact operator-facing form."""

    if not seeds:
        return "empty"
    if seeds == tuple(range(len(seeds))):
        return f"{seeds[0]}..{seeds[-1]} ({len(seeds)} seeds)"
    return f"{seeds!r} ({len(seeds)} seeds)"


def format_mission3_training_report(
    training_run: Phase5TrainingRun,
    *,
    artifact_root: Path,
) -> str:
    """Render a Mission-3-local training report over the accepted learner core."""

    checkpoint_lines = [
        (
            f"episode={checkpoint.checkpoint_episode} "
            f"checkpoint_step={checkpoint.checkpoint_step} "
            f"wins={checkpoint.model_selection_metrics.victory_count}/"
            f"{checkpoint.model_selection_metrics.episode_count} "
            f"path={checkpoint.checkpoint_path}"
        )
        for checkpoint in training_run.checkpoints
    ]
    return "\n".join(
        (
            "Mission 3 learned-policy training",
            f"learned_surface: {MISSION3_OBSERVATION_BASED_SURFACE}",
            f"artifact_root_policy: {artifact_root}",
            f"artifact_dir: {training_run.artifact_dir}",
            f"training_seed: {training_run.config.training_seed}",
            (
                "rollout_seed_formula: "
                "mission3_training_rollout_seed(training_seed, episode_index)"
            ),
            f"feature_adapter_seed: {training_run.config.feature_adapter_seed}",
            (
                "model_selection_seed_set: "
                f"{format_seed_set(training_run.config.model_selection_seeds)}"
            ),
            f"hidden_dim: {training_run.config.hidden_dim}",
            f"learning_rate: {training_run.config.learning_rate:.6f}",
            f"discount: {training_run.config.discount:.3f}",
            f"value_loss_coef: {training_run.config.value_loss_coef:.3f}",
            f"entropy_coef: {training_run.config.entropy_coef:.3f}",
            f"gradient_clip_norm: {training_run.config.gradient_clip_norm:.3f}",
            f"checkpoint_selection_policy: {PHASE5_CHECKPOINT_SELECTION_POLICY}",
            f"episodes: {training_run.config.total_episodes}",
            f"env_steps: {training_run.total_env_steps}",
            f"invalid_action_count: {training_run.invalid_action_count}",
            f"selected_checkpoint: {training_run.selected_checkpoint_path}",
            f"selected_checkpoint_episode: {training_run.selected_checkpoint_episode}",
            f"selected_checkpoint_step: {training_run.selected_checkpoint_step}",
            f"summary_path: {training_run.summary_path}",
            f"report_path: {training_run.report_path}",
            "",
            "Selected checkpoint model-selection metrics:",
            format_metrics_table((training_run.selected_model_selection_metrics,)),
            "",
            "Checkpoint sweep:",
            *(checkpoint_lines or ("none",)),
        ),
    )


def format_mission3_eval_report(
    *,
    mode: Mission3LearnedPolicyEvalMode,
    checkpoint_path: str,
    metrics: EpisodeMetrics,
    seeds: tuple[int, ...],
    checkpoint_metadata: Mission3EvalCheckpointMetadata | None = None,
) -> str:
    """Render a Mission 3 learned-policy report with explicit history framing."""

    comparison = build_mission3_historical_comparison(mode=mode, metrics=metrics)
    return "\n".join(
        line
        for line in (
            "Mission 3 learned-policy evaluation",
            f"mode: {mode}",
            f"checkpoint: {checkpoint_path}",
            (
                f"training_seed: {checkpoint_metadata.training_seed}"
                if checkpoint_metadata is not None
                else None
            ),
            (
                f"checkpoint_episode: {checkpoint_metadata.checkpoint_episode}"
                if checkpoint_metadata is not None
                else None
            ),
            (
                f"checkpoint_step: {checkpoint_metadata.checkpoint_step}"
                if checkpoint_metadata is not None
                else None
            ),
            (
                "checkpoint_model_selection_seed_set: "
                f"{format_seed_set(checkpoint_metadata.model_selection_seeds)}"
                if checkpoint_metadata is not None
                else None
            ),
            (
                "checkpoint_selection_policy: "
                f"{checkpoint_metadata.checkpoint_selection_policy}"
                if checkpoint_metadata is not None
                else None
            ),
            f"seed_set: {format_seed_set(seeds)}",
            f"learned_surface: {MISSION3_OBSERVATION_BASED_SURFACE}",
            (
                "historical_reference_qualification: "
                f"{MISSION3_HISTORICAL_REFERENCE_QUALIFICATION}"
            ),
            "",
            "Observation-based learned metrics:",
            format_metrics_table((metrics,)),
            "",
            "Preserved historical Mission 3 references:",
            f"random_wins: {comparison.random_reference_wins}",
            f"heuristic_wins: {comparison.heuristic_reference_wins}",
            f"rollout_search_wins: {comparison.rollout_search_reference_wins}",
            "",
            "Descriptive win deltas vs preserved history:",
            f"wins_vs_random: {comparison.wins_vs_random:+d}",
            (
                "wins_vs_heuristic_reference: "
                f"{comparison.wins_vs_heuristic_reference:+d}"
            ),
            (
                "wins_vs_rollout_search_reference: "
                f"{comparison.wins_vs_rollout_search_reference:+d}"
            ),
        )
        if line is not None
    )


def mission3_eval_payload(
    *,
    mode: Mission3LearnedPolicyEvalMode,
    checkpoint_path: str,
    metrics: EpisodeMetrics,
    seeds: tuple[int, ...],
    checkpoint_metadata: Mission3EvalCheckpointMetadata | None = None,
) -> dict[str, Any]:
    """Build a machine-readable Mission 3 learned-policy evaluation payload."""

    comparison = build_mission3_historical_comparison(mode=mode, metrics=metrics)
    payload: dict[str, Any] = {
        "mode": mode,
        "checkpoint_path": checkpoint_path,
        "seed_set": list(seeds),
        "learned_surface": {
            "contract": MISSION3_OBSERVATION_BASED_SURFACE,
        },
        "metrics": episode_metrics_payload(metrics),
        "preserved_historical_references": {
            "random_wins": comparison.random_reference_wins,
            "heuristic_wins": comparison.heuristic_reference_wins,
            "rollout_search_wins": comparison.rollout_search_reference_wins,
            "qualification": MISSION3_HISTORICAL_REFERENCE_QUALIFICATION,
        },
        "descriptive_win_deltas": {
            "wins_vs_random": comparison.wins_vs_random,
            "wins_vs_heuristic_reference": comparison.wins_vs_heuristic_reference,
            "wins_vs_rollout_search_reference": (
                comparison.wins_vs_rollout_search_reference
            ),
        },
    }
    if checkpoint_metadata is not None:
        payload["checkpoint_metadata"] = {
            "training_seed": checkpoint_metadata.training_seed,
            "checkpoint_episode": checkpoint_metadata.checkpoint_episode,
            "checkpoint_step": checkpoint_metadata.checkpoint_step,
            "model_selection_seeds": list(checkpoint_metadata.model_selection_seeds),
            "checkpoint_selection_policy": checkpoint_metadata.checkpoint_selection_policy,
        }
    return payload


def episode_metrics_payload(metrics: EpisodeMetrics) -> dict[str, Any]:
    """Convert one metrics row into a stable machine-readable payload."""

    return {
        "agent_name": metrics.agent_name,
        "episode_count": metrics.episode_count,
        "victory_count": metrics.victory_count,
        "defeat_count": metrics.defeat_count,
        "win_rate": metrics.win_rate,
        "defeat_rate": metrics.defeat_rate,
        "mean_terminal_turn": metrics.mean_terminal_turn,
        "mean_resolved_marker_count": metrics.mean_resolved_marker_count,
        "mean_removed_german_count": metrics.mean_removed_german_count,
        "mean_player_decision_count": metrics.mean_player_decision_count,
    }


def episode_metrics_from_payload(payload: dict[str, Any]) -> EpisodeMetrics:
    """Rebuild one metrics row from a machine-readable payload."""

    return EpisodeMetrics(
        agent_name=str(payload["agent_name"]),
        episode_count=int(payload["episode_count"]),
        victory_count=int(payload["victory_count"]),
        defeat_count=int(payload["defeat_count"]),
        win_rate=float(payload["win_rate"]),
        defeat_rate=float(payload["defeat_rate"]),
        mean_terminal_turn=float(payload["mean_terminal_turn"]),
        mean_resolved_marker_count=float(payload["mean_resolved_marker_count"]),
        mean_removed_german_count=float(payload["mean_removed_german_count"]),
        mean_player_decision_count=float(payload["mean_player_decision_count"]),
    )


__all__ = [
    "MISSION3_HISTORICAL_REFERENCE_QUALIFICATION",
    "MISSION3_OBSERVATION_BASED_SURFACE",
    "Mission3EvalCheckpointMetadata",
    "Mission3HistoricalComparison",
    "Mission3HistoricalReference",
    "Mission3LearnedPolicyEvalMode",
    "accepted_mission3_historical_reference",
    "build_mission3_historical_comparison",
    "episode_metrics_from_payload",
    "episode_metrics_payload",
    "format_mission3_eval_report",
    "format_mission3_training_report",
    "format_seed_set",
    "mission3_eval_payload",
]
