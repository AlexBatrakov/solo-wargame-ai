"""Compact Phase 5 reporting helpers for learned-policy comparisons."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from solo_wargame_ai.eval.metrics import EpisodeMetrics, format_metrics_table

Phase5EvalMode = Literal["smoke", "benchmark"]


@dataclass(frozen=True, slots=True)
class Phase5AnchorReference:
    """Accepted Phase 3 anchor wins preserved for Phase 5 comparison."""

    mode: Phase5EvalMode
    episode_count: int
    random_wins: int
    heuristic_wins: int


@dataclass(frozen=True, slots=True)
class Phase5AnchorComparison:
    """Learned-policy win deltas against the preserved Phase 3 anchors."""

    mode: Phase5EvalMode
    episode_count: int
    random_reference_wins: int
    heuristic_reference_wins: int
    wins_vs_random: int
    wins_vs_heuristic: int


@dataclass(frozen=True, slots=True)
class Phase5EvalCheckpointMetadata:
    """Checkpoint metadata surfaced into Phase 5 learned-policy reporting."""

    training_seed: int
    checkpoint_episode: int
    checkpoint_step: int
    model_selection_seeds: tuple[int, ...]
    checkpoint_selection_policy: str


def accepted_phase3_anchor(mode: Phase5EvalMode) -> Phase5AnchorReference:
    """Return the preserved Phase 3 anchor for the requested Phase 5 mode."""

    if mode == "smoke":
        return Phase5AnchorReference(
            mode=mode,
            episode_count=16,
            random_wins=2,
            heuristic_wins=11,
        )
    if mode == "benchmark":
        return Phase5AnchorReference(
            mode=mode,
            episode_count=200,
            random_wins=11,
            heuristic_wins=157,
        )
    raise ValueError(f"Unsupported Phase 5 evaluation mode: {mode!r}")


def build_phase5_anchor_comparison(
    *,
    mode: Phase5EvalMode,
    metrics: EpisodeMetrics,
) -> Phase5AnchorComparison:
    """Compare learned-policy wins against the preserved Phase 3 anchors."""

    anchor = accepted_phase3_anchor(mode)
    if metrics.episode_count != anchor.episode_count:
        raise ValueError(
            "Phase 5 evaluation metrics do not match the accepted episode count "
            f"for mode {mode!r}: expected {anchor.episode_count}, got {metrics.episode_count}",
        )
    return Phase5AnchorComparison(
        mode=mode,
        episode_count=anchor.episode_count,
        random_reference_wins=anchor.random_wins,
        heuristic_reference_wins=anchor.heuristic_wins,
        wins_vs_random=metrics.victory_count - anchor.random_wins,
        wins_vs_heuristic=metrics.victory_count - anchor.heuristic_wins,
    )


def format_seed_set(seeds: tuple[int, ...]) -> str:
    """Render one fixed seed tuple in the same compact style as Phase 3."""

    if not seeds:
        return "empty"
    if seeds == tuple(range(len(seeds))):
        return f"{seeds[0]}..{seeds[-1]} ({len(seeds)} seeds)"
    return f"{seeds!r} ({len(seeds)} seeds)"


def format_phase5_eval_report(
    *,
    mode: Phase5EvalMode,
    checkpoint_path: str,
    metrics: EpisodeMetrics,
    seeds: tuple[int, ...],
    checkpoint_metadata: Phase5EvalCheckpointMetadata | None = None,
) -> str:
    """Render a compact learned-policy evaluation report for operators."""

    comparison = build_phase5_anchor_comparison(mode=mode, metrics=metrics)
    return "\n".join(
        line
        for line in (
            "Phase 5 learned-policy evaluation",
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
            "",
            "Metrics table:",
            format_metrics_table((metrics,)),
            "",
            "Accepted Phase 3 win anchors:",
            f"random_wins: {comparison.random_reference_wins}",
            f"heuristic_wins: {comparison.heuristic_reference_wins}",
            "",
            "Win deltas against accepted anchors:",
            f"wins_vs_random: {comparison.wins_vs_random:+d}",
            f"wins_vs_heuristic: {comparison.wins_vs_heuristic:+d}",
        )
        if line is not None
    )


def phase5_eval_payload(
    *,
    mode: Phase5EvalMode,
    checkpoint_path: str,
    metrics: EpisodeMetrics,
    seeds: tuple[int, ...],
    checkpoint_metadata: Phase5EvalCheckpointMetadata | None = None,
) -> dict[str, Any]:
    """Build a machine-readable payload for one learned-policy evaluation."""

    comparison = build_phase5_anchor_comparison(mode=mode, metrics=metrics)
    payload: dict[str, Any] = {
        "mode": mode,
        "checkpoint_path": checkpoint_path,
        "seed_set": list(seeds),
        "metrics": episode_metrics_payload(metrics),
        "accepted_phase3_anchor": {
            "random_wins": comparison.random_reference_wins,
            "heuristic_wins": comparison.heuristic_reference_wins,
        },
        "win_deltas": {
            "wins_vs_random": comparison.wins_vs_random,
            "wins_vs_heuristic": comparison.wins_vs_heuristic,
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
    "Phase5AnchorComparison",
    "Phase5AnchorReference",
    "Phase5EvalCheckpointMetadata",
    "Phase5EvalMode",
    "accepted_phase3_anchor",
    "build_phase5_anchor_comparison",
    "episode_metrics_from_payload",
    "episode_metrics_payload",
    "format_phase5_eval_report",
    "format_seed_set",
    "phase5_eval_payload",
]
