"""Bounded Phase 5 training and checkpoint helpers for the first learner."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from random import Random
from typing import Any

from solo_wargame_ai.domain.mission import Mission
from solo_wargame_ai.env import Mission1Env
from solo_wargame_ai.eval.learned_policy_eval import evaluate_learned_policy
from solo_wargame_ai.eval.metrics import EpisodeMetrics, format_metrics_table
from solo_wargame_ai.eval.phase5_reporting import format_seed_set
from solo_wargame_ai.eval.phase5_seed_policy import (
    PHASE5_BENCHMARK_EVAL_SEEDS,
    PHASE5_FEATURE_ADAPTER_SEED,
    PHASE5_MODEL_SELECTION_SEEDS,
    PHASE5_SMOKE_EVAL_SEEDS,
    PHASE5_TRAINING_SEEDS,
    training_rollout_seed,
)

from .feature_adapter import ObservationFeatureAdapter
from .learned_policy import legal_action_ids_from_info, legal_action_mask_from_info
from .masked_action_selection import ActionMaskError, select_masked_action
from .masked_actor_critic import MaskedActorCriticNetwork, MaskedActorCriticPolicy

try:
    import torch
    from torch.nn import functional as F
except ModuleNotFoundError:  # pragma: no cover - exercised only without torch installed.
    torch = None
    F = None


DEFAULT_PHASE5_OUTPUT_ROOT = Path("outputs") / "phase5"
PHASE5_CHECKPOINT_SELECTION_POLICY = (
    "best greedy masked win count on fixed disjoint model-selection seeds; "
    "ties keep earliest checkpoint"
)


@dataclass(frozen=True, slots=True)
class Phase5TrainingConfig:
    """Bounded configuration surface for one Phase 5 training run."""

    training_seed: int
    total_episodes: int
    checkpoint_interval: int
    hidden_dim: int = 128
    learning_rate: float = 1e-3
    discount: float = 1.0
    value_loss_coef: float = 0.5
    entropy_coef: float = 0.01
    gradient_clip_norm: float = 1.0
    feature_adapter_seed: int = PHASE5_FEATURE_ADAPTER_SEED
    model_selection_seeds: tuple[int, ...] = PHASE5_MODEL_SELECTION_SEEDS

    def __post_init__(self) -> None:
        if self.training_seed not in PHASE5_TRAINING_SEEDS:
            raise ValueError(
                "Phase5TrainingConfig.training_seed must be one of the accepted "
                f"training seeds {PHASE5_TRAINING_SEEDS!r}",
            )
        if self.total_episodes < 1:
            raise ValueError("Phase5TrainingConfig.total_episodes must be positive")
        if self.checkpoint_interval < 1:
            raise ValueError("Phase5TrainingConfig.checkpoint_interval must be positive")
        if self.hidden_dim < 1:
            raise ValueError("Phase5TrainingConfig.hidden_dim must be positive")
        if self.learning_rate <= 0.0:
            raise ValueError("Phase5TrainingConfig.learning_rate must be positive")
        if not 0.0 < self.discount <= 1.0:
            raise ValueError("Phase5TrainingConfig.discount must be in the range (0, 1]")
        if self.value_loss_coef < 0.0:
            raise ValueError("Phase5TrainingConfig.value_loss_coef must be non-negative")
        if self.entropy_coef < 0.0:
            raise ValueError("Phase5TrainingConfig.entropy_coef must be non-negative")
        if self.gradient_clip_norm <= 0.0:
            raise ValueError("Phase5TrainingConfig.gradient_clip_norm must be positive")
        if not self.model_selection_seeds:
            raise ValueError("Phase5TrainingConfig.model_selection_seeds must not be empty")
        _validate_model_selection_seeds(self)


@dataclass(frozen=True, slots=True)
class Phase5CheckpointRecord:
    """One saved checkpoint plus its fixed model-selection metrics."""

    checkpoint_path: Path
    checkpoint_episode: int
    checkpoint_step: int
    model_selection_metrics: EpisodeMetrics


@dataclass(frozen=True, slots=True)
class Phase5TrainingRun:
    """Completed bounded training run with a selected checkpoint."""

    config: Phase5TrainingConfig
    artifact_dir: Path
    checkpoint_dir: Path
    summary_path: Path
    report_path: Path
    total_env_steps: int
    invalid_action_count: int
    checkpoints: tuple[Phase5CheckpointRecord, ...]
    selected_checkpoint_path: Path
    selected_checkpoint_episode: int
    selected_checkpoint_step: int
    selected_model_selection_metrics: EpisodeMetrics


@dataclass(frozen=True, slots=True)
class LoadedPhase5Checkpoint:
    """Loaded checkpoint assets required for Phase 5 evaluation."""

    checkpoint_path: Path
    mission_id: str
    training_seed: int
    checkpoint_episode: int
    checkpoint_step: int
    feature_adapter_seed: int
    hidden_dim: int
    action_count: int
    model_selection_seeds: tuple[int, ...]
    checkpoint_selection_policy: str
    model_selection_metrics: EpisodeMetrics | None
    adapter: ObservationFeatureAdapter
    model: MaskedActorCriticNetwork


def build_phase5_feature_adapter(
    mission: Mission,
    *,
    feature_adapter_seed: int = PHASE5_FEATURE_ADAPTER_SEED,
) -> ObservationFeatureAdapter:
    """Build the fixed observation adapter from a disjoint dedicated seed."""

    env = Mission1Env(mission)
    initial_observation, _ = env.reset(seed=feature_adapter_seed)
    return ObservationFeatureAdapter.from_initial_observation(initial_observation)


def default_phase5_output_dir(
    config: Phase5TrainingConfig,
    *,
    output_root: Path = DEFAULT_PHASE5_OUTPUT_ROOT,
) -> Path:
    """Return the default artifact directory for one bounded training run."""

    return output_root / (
        f"train_seed_{config.training_seed}_ep_{config.total_episodes}"
    )


def train_masked_actor_critic(
    mission: Mission,
    *,
    config: Phase5TrainingConfig,
    output_dir: Path | None = None,
    overwrite_output_dir: bool = False,
) -> Phase5TrainingRun:
    """Run one bounded terminal-only training pass with fixed checkpoint selection."""

    if torch is None or F is None:
        raise ModuleNotFoundError(
            "train_masked_actor_critic requires the optional torch dependency",
        )

    artifact_dir = default_phase5_output_dir(config) if output_dir is None else output_dir
    _prepare_output_dir(
        artifact_dir,
        overwrite_output_dir=overwrite_output_dir,
    )
    checkpoint_dir = artifact_dir / "checkpoints"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    torch.manual_seed(config.training_seed)
    adapter = build_phase5_feature_adapter(
        mission,
        feature_adapter_seed=config.feature_adapter_seed,
    )
    model = MaskedActorCriticNetwork(
        input_dim=adapter.feature_size,
        action_count=_action_count_for_mission(mission),
        hidden_dim=config.hidden_dim,
    )
    optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)
    action_rng = Random(config.training_seed)
    env = Mission1Env(mission)

    checkpoints: list[Phase5CheckpointRecord] = []
    total_env_steps = 0
    invalid_action_count = 0
    selected_checkpoint: Phase5CheckpointRecord | None = None
    selected_checkpoint_alias_path = checkpoint_dir / "selected_checkpoint.pt"

    for episode_index in range(config.total_episodes):
        model.train()
        observation, info = env.reset(
            seed=training_rollout_seed(config.training_seed, episode_index),
        )
        rewards: list[float] = []
        step_log_probs = []
        step_values = []
        step_entropies = []
        terminated = False
        truncated = False

        while not (terminated or truncated):
            action_id, log_prob, entropy, value_estimate = _training_action_step(
                model,
                adapter,
                observation,
                info,
                rng=action_rng,
            )
            legal_action_ids = legal_action_ids_from_info(info)
            if action_id not in legal_action_ids:
                invalid_action_count += 1
                raise ActionMaskError(
                    "Masked actor-critic training produced an illegal action id "
                    f"{action_id} outside {legal_action_ids!r}",
                )

            observation, reward, terminated, truncated, info = env.step(action_id)
            rewards.append(float(reward))
            step_log_probs.append(log_prob)
            step_values.append(value_estimate)
            step_entropies.append(entropy)
            total_env_steps += 1

        if truncated:
            raise RuntimeError(
                "Phase 5 training does not accept truncated episodes in default mode",
            )

        _optimize_episode(
            optimizer,
            step_log_probs=step_log_probs,
            step_values=step_values,
            step_entropies=step_entropies,
            rewards=rewards,
            config=config,
        )

        checkpoint_episode = episode_index + 1
        if (
            checkpoint_episode % config.checkpoint_interval == 0
            or checkpoint_episode == config.total_episodes
        ):
            checkpoint_record = _evaluate_and_save_checkpoint(
                mission=mission,
                adapter=adapter,
                model=model,
                config=config,
                checkpoint_dir=checkpoint_dir,
                checkpoint_episode=checkpoint_episode,
                checkpoint_step=total_env_steps,
            )
            checkpoints.append(checkpoint_record)
            if _is_better_checkpoint(
                candidate=checkpoint_record,
                current_best=selected_checkpoint,
            ):
                selected_checkpoint = checkpoint_record
                torch.save(
                    _checkpoint_payload(
                        mission=mission,
                        model=model,
                        config=config,
                        checkpoint_episode=checkpoint_record.checkpoint_episode,
                        checkpoint_step=checkpoint_record.checkpoint_step,
                        model_selection_metrics=checkpoint_record.model_selection_metrics,
                    ),
                    selected_checkpoint_alias_path,
                )

    if selected_checkpoint is None:
        raise RuntimeError("Phase 5 training finished without producing any checkpoint")

    training_run = Phase5TrainingRun(
        config=config,
        artifact_dir=artifact_dir,
        checkpoint_dir=checkpoint_dir,
        summary_path=artifact_dir / "training_summary.json",
        report_path=artifact_dir / "training_report.txt",
        total_env_steps=total_env_steps,
        invalid_action_count=invalid_action_count,
        checkpoints=tuple(checkpoints),
        selected_checkpoint_path=selected_checkpoint_alias_path,
        selected_checkpoint_episode=selected_checkpoint.checkpoint_episode,
        selected_checkpoint_step=selected_checkpoint.checkpoint_step,
        selected_model_selection_metrics=selected_checkpoint.model_selection_metrics,
    )
    _write_training_artifacts(training_run)
    return training_run


def load_phase5_checkpoint(
    mission: Mission,
    checkpoint_path: Path,
) -> LoadedPhase5Checkpoint:
    """Load one saved Phase 5 checkpoint into a reusable policy bundle."""

    if torch is None:
        raise ModuleNotFoundError(
            "load_phase5_checkpoint requires the optional torch dependency",
        )

    payload = torch.load(checkpoint_path, map_location="cpu")
    format_version = int(payload["format_version"])
    if format_version not in (1, 2):
        raise ValueError(
            "Unsupported Phase 5 checkpoint format version: "
            f"{payload['format_version']!r}",
        )
    mission_id = str(payload["mission_id"])
    if mission.mission_id != mission_id:
        raise ValueError(
            "Checkpoint mission mismatch: "
            f"expected {mission_id!r}, got {mission.mission_id!r}",
        )

    adapter = build_phase5_feature_adapter(
        mission,
        feature_adapter_seed=int(payload["feature_adapter_seed"]),
    )
    action_count = int(payload["action_count"])
    model = MaskedActorCriticNetwork(
        input_dim=adapter.feature_size,
        action_count=action_count,
        hidden_dim=int(payload["hidden_dim"]),
    )
    model.load_state_dict(payload["model_state_dict"])
    model.eval()

    metrics_payload = payload.get("model_selection_metrics")
    return LoadedPhase5Checkpoint(
        checkpoint_path=Path(checkpoint_path),
        mission_id=mission_id,
        training_seed=int(payload["training_seed"]),
        checkpoint_episode=int(payload["checkpoint_episode"]),
        checkpoint_step=int(payload["checkpoint_step"]),
        feature_adapter_seed=int(payload["feature_adapter_seed"]),
        hidden_dim=int(payload["hidden_dim"]),
        action_count=action_count,
        model_selection_seeds=tuple(
            int(seed)
            for seed in payload.get("model_selection_seeds", PHASE5_MODEL_SELECTION_SEEDS)
        ),
        checkpoint_selection_policy=str(
            payload.get(
                "checkpoint_selection_policy",
                PHASE5_CHECKPOINT_SELECTION_POLICY,
            ),
        ),
        model_selection_metrics=(
            None if metrics_payload is None else _episode_metrics_from_payload(metrics_payload)
        ),
        adapter=adapter,
        model=model,
    )


def build_phase5_policy_factory(
    mission: Mission,
    checkpoint_path: Path,
):
    """Build a policy factory that reuses one loaded checkpoint for evaluation."""

    loaded_checkpoint = load_phase5_checkpoint(mission, checkpoint_path)

    def factory() -> MaskedActorCriticPolicy:
        return MaskedActorCriticPolicy(
            loaded_checkpoint.adapter,
            loaded_checkpoint.model,
            seed=loaded_checkpoint.training_seed,
        )

    return factory


def format_phase5_training_report(training_run: Phase5TrainingRun) -> str:
    """Render a compact operator-facing training report."""

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
            "Phase 5 training",
            f"training_seed: {training_run.config.training_seed}",
            (
                "rollout_seed_formula: "
                f"training_rollout_seed({training_run.config.training_seed}, episode_index)"
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


def _action_count_for_mission(mission: Mission) -> int:
    env = Mission1Env(mission)
    return env.action_space_size


def _training_action_step(
    model: MaskedActorCriticNetwork,
    adapter: ObservationFeatureAdapter,
    observation,
    info,
    *,
    rng: Random,
):
    if torch is None:
        raise ModuleNotFoundError(
            "_training_action_step requires the optional torch dependency",
        )

    feature_vector = adapter.encode(observation)
    policy_logits, values = model.forward(feature_vector.values)
    logits = policy_logits[0]
    value_estimate = values[0]
    legal_action_mask = legal_action_mask_from_info(info)
    legal_action_ids = tuple(
        action_id
        for action_id, is_legal in enumerate(legal_action_mask)
        if is_legal
    )
    if not legal_action_ids:
        raise ActionMaskError("training action step requires at least one legal action id")

    selection = select_masked_action(
        tuple(float(logit) for logit in logits.detach().tolist()),
        legal_action_mask,
        evaluation=False,
        rng=rng,
    )
    local_index = legal_action_ids.index(selection.action_id)
    masked_logits = logits[list(legal_action_ids)]
    masked_log_probs = torch.log_softmax(masked_logits, dim=0)
    probabilities = torch.softmax(masked_logits, dim=0)
    entropy = -(probabilities * masked_log_probs).sum()
    log_prob = masked_log_probs[local_index]
    return selection.action_id, log_prob, entropy, value_estimate


def _optimize_episode(
    optimizer,
    *,
    step_log_probs,
    step_values,
    step_entropies,
    rewards: list[float],
    config: Phase5TrainingConfig,
) -> None:
    if torch is None or F is None:
        raise ModuleNotFoundError("_optimize_episode requires the optional torch dependency")

    returns: list[float] = []
    running_return = 0.0
    for reward in reversed(rewards):
        running_return = reward + (config.discount * running_return)
        returns.append(running_return)
    returns.reverse()

    returns_tensor = torch.tensor(returns, dtype=torch.float32)
    log_probs_tensor = torch.stack(step_log_probs)
    values_tensor = torch.stack(step_values)
    entropies_tensor = torch.stack(step_entropies)
    advantages = returns_tensor - values_tensor.detach()

    policy_loss = -(log_probs_tensor * advantages).mean()
    value_loss = F.mse_loss(values_tensor, returns_tensor)
    entropy_bonus = entropies_tensor.mean()
    total_loss = (
        policy_loss
        + (config.value_loss_coef * value_loss)
        - (config.entropy_coef * entropy_bonus)
    )

    optimizer.zero_grad(set_to_none=True)
    total_loss.backward()
    torch.nn.utils.clip_grad_norm_(
        _model_parameters(optimizer),
        max_norm=config.gradient_clip_norm,
    )
    optimizer.step()


def _evaluate_and_save_checkpoint(
    *,
    mission: Mission,
    adapter: ObservationFeatureAdapter,
    model: MaskedActorCriticNetwork,
    config: Phase5TrainingConfig,
    checkpoint_dir: Path,
    checkpoint_episode: int,
    checkpoint_step: int,
) -> Phase5CheckpointRecord:
    checkpoint_path = checkpoint_dir / f"checkpoint_ep_{checkpoint_episode:05d}.pt"
    model_selection_metrics = _evaluate_model_selection_metrics(
        mission=mission,
        adapter=adapter,
        model=model,
        config=config,
    )
    torch.save(
        _checkpoint_payload(
            mission=mission,
            model=model,
            config=config,
            checkpoint_episode=checkpoint_episode,
            checkpoint_step=checkpoint_step,
            model_selection_metrics=model_selection_metrics,
        ),
        checkpoint_path,
    )
    return Phase5CheckpointRecord(
        checkpoint_path=checkpoint_path,
        checkpoint_episode=checkpoint_episode,
        checkpoint_step=checkpoint_step,
        model_selection_metrics=model_selection_metrics,
    )


def _evaluate_model_selection_metrics(
    *,
    mission: Mission,
    adapter: ObservationFeatureAdapter,
    model: MaskedActorCriticNetwork,
    config: Phase5TrainingConfig,
) -> EpisodeMetrics:
    model.eval()
    with torch.no_grad():
        evaluation = evaluate_learned_policy(
            mission,
            policy_factory=lambda: MaskedActorCriticPolicy(
                adapter,
                model,
                seed=config.training_seed,
            ),
            seeds=config.model_selection_seeds,
            evaluation=True,
        )
    return evaluation.metrics


def _prepare_output_dir(
    artifact_dir: Path,
    *,
    overwrite_output_dir: bool,
) -> None:
    if artifact_dir.exists():
        if not artifact_dir.is_dir():
            raise NotADirectoryError(
                f"Phase 5 output path must be a directory: {artifact_dir}",
            )
        if any(artifact_dir.iterdir()):
            if not overwrite_output_dir:
                raise FileExistsError(
                    "Phase 5 output dir already exists and is not empty: "
                    f"{artifact_dir}. Pass overwrite_output_dir=True to replace it.",
                )
            shutil.rmtree(artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)


def _is_better_checkpoint(
    *,
    candidate: Phase5CheckpointRecord,
    current_best: Phase5CheckpointRecord | None,
) -> bool:
    if current_best is None:
        return True
    if (
        candidate.model_selection_metrics.victory_count
        != current_best.model_selection_metrics.victory_count
    ):
        return (
            candidate.model_selection_metrics.victory_count
            > current_best.model_selection_metrics.victory_count
        )
    return candidate.checkpoint_step < current_best.checkpoint_step


def _checkpoint_payload(
    *,
    mission: Mission,
    model: MaskedActorCriticNetwork,
    config: Phase5TrainingConfig,
    checkpoint_episode: int,
    checkpoint_step: int,
    model_selection_metrics: EpisodeMetrics | None,
) -> dict[str, Any]:
    return {
        "format_version": 2,
        "mission_id": mission.mission_id,
        "training_seed": config.training_seed,
        "checkpoint_episode": checkpoint_episode,
        "checkpoint_step": checkpoint_step,
        "feature_adapter_seed": config.feature_adapter_seed,
        "hidden_dim": config.hidden_dim,
        "learning_rate": config.learning_rate,
        "discount": config.discount,
        "value_loss_coef": config.value_loss_coef,
        "entropy_coef": config.entropy_coef,
        "gradient_clip_norm": config.gradient_clip_norm,
        "action_count": _action_count_for_mission(mission),
        "model_selection_seeds": list(config.model_selection_seeds),
        "checkpoint_selection_policy": PHASE5_CHECKPOINT_SELECTION_POLICY,
        "model_selection_metrics": (
            None
            if model_selection_metrics is None
            else _episode_metrics_payload(model_selection_metrics)
        ),
        "model_state_dict": model.state_dict(),
    }


def _episode_metrics_payload(metrics: EpisodeMetrics) -> dict[str, Any]:
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


def _episode_metrics_from_payload(payload: dict[str, Any]) -> EpisodeMetrics:
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


def _write_training_artifacts(training_run: Phase5TrainingRun) -> None:
    training_run.artifact_dir.mkdir(parents=True, exist_ok=True)
    training_run.summary_path.write_text(
        json.dumps(_training_run_payload(training_run), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    training_run.report_path.write_text(
        format_phase5_training_report(training_run) + "\n",
        encoding="utf-8",
    )


def _training_run_payload(training_run: Phase5TrainingRun) -> dict[str, Any]:
    return {
        "training_seed": training_run.config.training_seed,
        "feature_adapter_seed": training_run.config.feature_adapter_seed,
        "model_selection_seeds": list(training_run.config.model_selection_seeds),
        "hidden_dim": training_run.config.hidden_dim,
        "learning_rate": training_run.config.learning_rate,
        "discount": training_run.config.discount,
        "value_loss_coef": training_run.config.value_loss_coef,
        "entropy_coef": training_run.config.entropy_coef,
        "gradient_clip_norm": training_run.config.gradient_clip_norm,
        "checkpoint_selection_policy": PHASE5_CHECKPOINT_SELECTION_POLICY,
        "episodes": training_run.config.total_episodes,
        "env_steps": training_run.total_env_steps,
        "invalid_action_count": training_run.invalid_action_count,
        "selected_checkpoint_path": str(training_run.selected_checkpoint_path),
        "selected_checkpoint_episode": training_run.selected_checkpoint_episode,
        "selected_checkpoint_step": training_run.selected_checkpoint_step,
        "selected_model_selection_metrics": _episode_metrics_payload(
            training_run.selected_model_selection_metrics,
        ),
        "checkpoints": [
            {
                "checkpoint_path": str(checkpoint.checkpoint_path),
                "checkpoint_episode": checkpoint.checkpoint_episode,
                "checkpoint_step": checkpoint.checkpoint_step,
                "model_selection_metrics": _episode_metrics_payload(
                    checkpoint.model_selection_metrics,
                ),
            }
            for checkpoint in training_run.checkpoints
        ],
    }


def _model_parameters(optimizer) -> list[object]:
    """Flatten optimizer parameter groups for gradient clipping."""

    return [
        parameter
        for parameter_group in optimizer.param_groups
        for parameter in parameter_group["params"]
    ]


def _validate_model_selection_seeds(config: Phase5TrainingConfig) -> None:
    duplicates = len(set(config.model_selection_seeds)) != len(config.model_selection_seeds)
    if duplicates:
        raise ValueError("Phase5TrainingConfig.model_selection_seeds must not contain duplicates")

    overlap_with_smoke = set(config.model_selection_seeds) & set(PHASE5_SMOKE_EVAL_SEEDS)
    if overlap_with_smoke:
        raise ValueError(
            "Phase5TrainingConfig.model_selection_seeds must not overlap the accepted "
            f"smoke eval seeds: {sorted(overlap_with_smoke)!r}",
        )

    overlap_with_benchmark = set(config.model_selection_seeds) & set(PHASE5_BENCHMARK_EVAL_SEEDS)
    if overlap_with_benchmark:
        raise ValueError(
            "Phase5TrainingConfig.model_selection_seeds must not overlap the accepted "
            f"benchmark eval seeds: {sorted(overlap_with_benchmark)!r}",
        )

    rollout_seeds = {
        training_rollout_seed(config.training_seed, episode_index)
        for episode_index in range(config.total_episodes)
    }
    overlap_with_rollouts = set(config.model_selection_seeds) & rollout_seeds
    if overlap_with_rollouts:
        raise ValueError(
            "Phase5TrainingConfig.model_selection_seeds must not overlap rollout-only "
            f"training seeds: {sorted(overlap_with_rollouts)!r}",
        )

__all__ = [
    "DEFAULT_PHASE5_OUTPUT_ROOT",
    "LoadedPhase5Checkpoint",
    "PHASE5_CHECKPOINT_SELECTION_POLICY",
    "Phase5CheckpointRecord",
    "Phase5TrainingConfig",
    "Phase5TrainingRun",
    "build_phase5_feature_adapter",
    "build_phase5_policy_factory",
    "default_phase5_output_dir",
    "format_phase5_training_report",
    "load_phase5_checkpoint",
    "train_masked_actor_critic",
]
