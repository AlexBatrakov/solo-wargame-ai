"""Generic exact-backed mission summary helpers."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from solo_wargame_ai.agents.base import Agent
from solo_wargame_ai.domain.resolver import (
    apply_action,
    get_legal_actions,
    resolve_automatic_progression,
)
from solo_wargame_ai.domain.state import create_initial_game_state
from solo_wargame_ai.eval.episode_runner import run_episodes
from solo_wargame_ai.io import load_mission

from .exact_artifact import ExactArtifact, default_exact_artifact_dir, resolve_exact_db_path
from .exact_policy_solver import (
    EXACT_TIE_TOLERANCE_DEFAULT,
    action_label,
    build_capped_exact_policy_solver,
)
from .policy_audit import read_policy_audit_stats

ExactFixedSeedSource = Literal[
    "artifact_action_values",
    "full_solver_replay",
    "known_anchor_artifact_replay",
]


@dataclass(frozen=True, slots=True)
class KnownMissionExactAnchor:
    mission_id: str
    exact_full_space_ceiling: float
    exact_equivalent_200: float
    exact_fixed_seed_ceiling_wins: int
    benchmark_seed_count: int
    exact_fixed_seed_source: ExactFixedSeedSource
    exact_fixed_seed_caveat: str | None = None


@dataclass(frozen=True, slots=True)
class MissionSummary:
    mission_id: str
    mission_path: Path
    benchmark_seed_count: int
    exact_full_space_ceiling: float | None
    exact_equivalent_200: float | None
    exact_artifact_dir: Path | None
    exact_artifact_has_action_values: bool
    exact_fixed_seed_ceiling_wins: int | None
    exact_fixed_seed_ceiling_ratio: float | None
    exact_fixed_seed_source: ExactFixedSeedSource | None
    exact_fixed_seed_caveat: str | None
    policy_artifact_dir: Path | None
    policy_agent_name: str | None
    policy_full_probability_value: float | None
    policy_equivalent_200: float | None
    policy_seed_wins: int | None
    policy_seed_ratio: float | None
    policy_vs_exact_ceiling_ratio: float | None
    policy_vs_seed_ceiling_ratio: float | None

    def to_payload(self) -> dict[str, object]:
        return {
            "mission_id": self.mission_id,
            "mission_path": str(self.mission_path),
            "benchmark_seed_count": self.benchmark_seed_count,
            "exact_full_space_ceiling": self.exact_full_space_ceiling,
            "exact_equivalent_200": self.exact_equivalent_200,
            "exact_artifact_dir": (
                None
                if self.exact_artifact_dir is None
                else str(self.exact_artifact_dir)
            ),
            "exact_artifact_has_action_values": self.exact_artifact_has_action_values,
            "exact_fixed_seed_ceiling_wins": self.exact_fixed_seed_ceiling_wins,
            "exact_fixed_seed_ceiling_ratio": self.exact_fixed_seed_ceiling_ratio,
            "exact_fixed_seed_source": self.exact_fixed_seed_source,
            "exact_fixed_seed_caveat": self.exact_fixed_seed_caveat,
            "policy_artifact_dir": (
                None
                if self.policy_artifact_dir is None
                else str(self.policy_artifact_dir)
            ),
            "policy_agent_name": self.policy_agent_name,
            "policy_full_probability_value": self.policy_full_probability_value,
            "policy_equivalent_200": self.policy_equivalent_200,
            "policy_seed_wins": self.policy_seed_wins,
            "policy_seed_ratio": self.policy_seed_ratio,
            "policy_vs_exact_ceiling_ratio": self.policy_vs_exact_ceiling_ratio,
            "policy_vs_seed_ceiling_ratio": self.policy_vs_seed_ceiling_ratio,
        }


KNOWN_MISSION_EXACT_ANCHORS: dict[str, KnownMissionExactAnchor] = {
    "mission_02_secure_the_woods_2": KnownMissionExactAnchor(
        mission_id="mission_02_secure_the_woods_2",
        exact_full_space_ceiling=0.598931044695,
        exact_equivalent_200=119.786209,
        exact_fixed_seed_ceiling_wins=131,
        benchmark_seed_count=200,
        exact_fixed_seed_source="known_anchor_artifact_replay",
        exact_fixed_seed_caveat=(
            "Strong working anchor from artifact-backed deterministic replay via reconstructed "
            "Q*(s,a), but not yet as fully locked down as Mission 1 186/200."
        ),
    ),
}


def deterministic_exact_seed_wins_from_artifact(
    *,
    exact_artifact: ExactArtifact,
    mission_path: Path,
    seeds: tuple[int, ...],
    tolerance: float | None = None,
) -> int:
    """Replay deterministic exact-optimal seeds using exact action rows from an artifact."""

    mission = load_mission(mission_path)
    wins = 0
    for seed in seeds:
        state = create_initial_game_state(mission, seed=seed)
        while state.terminal_outcome is None:
            legal_actions = get_legal_actions(state)
            if not legal_actions:
                state = resolve_automatic_progression(state)
                continue
            if len(legal_actions) == 1:
                action = legal_actions[0]
            else:
                chosen_row = exact_artifact.lookup_exact_chosen_action_key(
                    exact_artifact.codec.pack_canonical(state),
                    tolerance=tolerance,
                )
                if chosen_row is None:
                    raise RuntimeError(
                        "exact artifact lacks action values for a multi-action state",
                    )
                chosen_label, chosen_repr, _chosen_q = chosen_row
                matching = [
                    candidate
                    for candidate in legal_actions
                    if action_label(candidate) == chosen_label and repr(candidate) == chosen_repr
                ]
                if not matching:
                    raise RuntimeError(
                        "exact artifact chosen action could not be matched to legal actions",
                    )
                action = matching[0]
            state = apply_action(state, action)
        if state.terminal_outcome.value == "victory":
            wins += 1
    return wins


def deterministic_exact_seed_wins_from_solver(
    *,
    mission_path: Path,
    seeds: tuple[int, ...],
    progress_interval_sec: float = 30.0,
    cap_metric: str = "auto",
    memory_cap_gb: float = 20.0,
    memory_low_water_gb: float = 17.0,
    trim_check_interval: int = 2048,
    min_trim_entries: int = 8192,
    cache_through_turn: int | None = None,
    tolerance: float = EXACT_TIE_TOLERANCE_DEFAULT,
) -> int:
    """Replay deterministic exact-optimal seeds using a live solver fallback."""

    mission = load_mission(mission_path)
    solver = build_capped_exact_policy_solver(
        mission_path=mission_path,
        progress_interval_sec=progress_interval_sec,
        cap_metric=cap_metric,
        memory_cap_gb=memory_cap_gb,
        memory_low_water_gb=memory_low_water_gb,
        trim_check_interval=trim_check_interval,
        min_trim_entries=min_trim_entries,
        cache_through_turn=cache_through_turn,
    )
    wins = 0
    for seed in seeds:
        state = create_initial_game_state(mission, seed=seed)
        while state.terminal_outcome is None:
            legal_actions = get_legal_actions(state)
            if not legal_actions:
                state = resolve_automatic_progression(state)
                continue
            if len(legal_actions) == 1:
                action = legal_actions[0]
            else:
                action_values = {action: solver.q_value(state, action) for action in legal_actions}
                best_value = max(action_values.values())
                best_actions = [
                    action
                    for action, value in action_values.items()
                    if best_value - value <= tolerance
                ]
                action = min(
                    best_actions,
                    key=lambda candidate: (action_label(candidate), repr(candidate)),
                )
            state = apply_action(state, action)
        if state.terminal_outcome.value == "victory":
            wins += 1
    solver.maybe_report_progress(force=True)
    return wins


def benchmark_policy_seed_wins(
    *,
    mission_path: Path,
    build_agent: Callable[[], Agent],
    seeds: tuple[int, ...],
) -> int:
    """Replay a fixed agent on a deterministic seed surface."""

    mission = load_mission(mission_path)
    episode_runs = run_episodes(
        mission,
        agent_factory=lambda _seed: build_agent(),
        seeds=seeds,
    )
    return sum(run.result.terminal_outcome.value == "victory" for run in episode_runs)


def build_mission_summary(
    *,
    mission_path: Path,
    exact_artifact_dir: Path | None = None,
    policy_artifact_dir: Path | None = None,
    build_agent: Callable[[], Agent] | None = None,
    agent_name: str | None = None,
    seed_stop: int = 200,
    allow_known_anchor: bool = True,
    allow_full_solver_replay: bool = False,
    progress_interval_sec: float = 30.0,
    cap_metric: str = "auto",
    memory_cap_gb: float = 20.0,
    memory_low_water_gb: float = 17.0,
    trim_check_interval: int = 2048,
    min_trim_entries: int = 8192,
    cache_through_turn: int | None = None,
) -> MissionSummary:
    """Build a summary from existing artifacts plus optional benchmark replay."""

    mission_path = Path(mission_path)
    mission = load_mission(mission_path)
    benchmark_seed_count = seed_stop
    seeds = tuple(range(seed_stop))
    known_anchor = (
        KNOWN_MISSION_EXACT_ANCHORS.get(mission.mission_id)
        if allow_known_anchor
        else None
    )

    exact_ceiling = None
    exact_equivalent_200 = None
    exact_artifact_has_action_values = False
    exact_seed_wins = None
    exact_seed_ratio = None
    exact_seed_source = None
    exact_seed_caveat = None
    resolved_exact_artifact_dir: Path | None = None

    if exact_artifact_dir is not None:
        resolved_exact_artifact_dir = Path(exact_artifact_dir)
    elif (default_exact_artifact_dir(mission_path) / "metadata.json").exists():
        resolved_exact_artifact_dir = default_exact_artifact_dir(mission_path)

    if resolved_exact_artifact_dir is not None:
        exact_artifact = ExactArtifact(
            db_path=resolve_exact_db_path(resolved_exact_artifact_dir),
            metadata_path=resolved_exact_artifact_dir / "metadata.json",
            mission_path=mission_path,
        )
        try:
            exact_ceiling = float(exact_artifact.metadata["root_value"])
            exact_equivalent_200 = exact_ceiling * 200.0
            exact_artifact_has_action_values = exact_artifact.has_action_values()
            if exact_artifact_has_action_values:
                exact_seed_wins = deterministic_exact_seed_wins_from_artifact(
                    exact_artifact=exact_artifact,
                    mission_path=mission_path,
                    seeds=seeds,
                )
                exact_seed_source = "artifact_action_values"
            elif allow_full_solver_replay:
                exact_seed_wins = deterministic_exact_seed_wins_from_solver(
                    mission_path=mission_path,
                    seeds=seeds,
                    progress_interval_sec=progress_interval_sec,
                    cap_metric=cap_metric,
                    memory_cap_gb=memory_cap_gb,
                    memory_low_water_gb=memory_low_water_gb,
                    trim_check_interval=trim_check_interval,
                    min_trim_entries=min_trim_entries,
                    cache_through_turn=cache_through_turn,
                )
                exact_seed_source = "full_solver_replay"
        finally:
            exact_artifact.close()
    elif known_anchor is not None:
        exact_ceiling = known_anchor.exact_full_space_ceiling
        exact_equivalent_200 = known_anchor.exact_equivalent_200
        if known_anchor.benchmark_seed_count == benchmark_seed_count:
            exact_seed_wins = known_anchor.exact_fixed_seed_ceiling_wins
            exact_seed_source = known_anchor.exact_fixed_seed_source
            exact_seed_caveat = known_anchor.exact_fixed_seed_caveat

    if (
        exact_seed_wins is None
        and known_anchor is not None
        and known_anchor.benchmark_seed_count == benchmark_seed_count
    ):
        exact_seed_wins = known_anchor.exact_fixed_seed_ceiling_wins
        exact_seed_source = known_anchor.exact_fixed_seed_source
        exact_seed_caveat = known_anchor.exact_fixed_seed_caveat

    if exact_seed_wins is not None:
        exact_seed_ratio = exact_seed_wins / benchmark_seed_count

    policy_full_probability_value = None
    policy_equivalent_200 = None
    policy_agent = agent_name
    resolved_policy_artifact_dir = (
        Path(policy_artifact_dir) if policy_artifact_dir is not None else None
    )
    if resolved_policy_artifact_dir is not None:
        metadata = read_policy_audit_stats(resolved_policy_artifact_dir)
        policy_full_probability_value = float(metadata["policy_root_value"])
        policy_equivalent_200 = policy_full_probability_value * 200.0
        if policy_agent is None:
            policy_agent = str(metadata["agent_name"])

    policy_seed_wins = None
    if build_agent is not None:
        policy_seed_wins = benchmark_policy_seed_wins(
            mission_path=mission_path,
            build_agent=build_agent,
            seeds=seeds,
        )

    policy_seed_ratio = (
        None
        if policy_seed_wins is None
        else policy_seed_wins / benchmark_seed_count
    )
    policy_vs_exact_ratio = None
    if policy_full_probability_value is not None and exact_ceiling not in (None, 0.0):
        policy_vs_exact_ratio = policy_full_probability_value / exact_ceiling
    policy_vs_seed_ratio = None
    if policy_seed_wins is not None and exact_seed_wins not in (None, 0):
        policy_vs_seed_ratio = policy_seed_wins / exact_seed_wins

    return MissionSummary(
        mission_id=mission.mission_id,
        mission_path=mission_path,
        benchmark_seed_count=benchmark_seed_count,
        exact_full_space_ceiling=exact_ceiling,
        exact_equivalent_200=exact_equivalent_200,
        exact_artifact_dir=resolved_exact_artifact_dir,
        exact_artifact_has_action_values=exact_artifact_has_action_values,
        exact_fixed_seed_ceiling_wins=exact_seed_wins,
        exact_fixed_seed_ceiling_ratio=exact_seed_ratio,
        exact_fixed_seed_source=exact_seed_source,
        exact_fixed_seed_caveat=exact_seed_caveat,
        policy_artifact_dir=resolved_policy_artifact_dir,
        policy_agent_name=policy_agent,
        policy_full_probability_value=policy_full_probability_value,
        policy_equivalent_200=policy_equivalent_200,
        policy_seed_wins=policy_seed_wins,
        policy_seed_ratio=policy_seed_ratio,
        policy_vs_exact_ceiling_ratio=policy_vs_exact_ratio,
        policy_vs_seed_ceiling_ratio=policy_vs_seed_ratio,
    )


def format_mission_summary_report(summary: MissionSummary) -> str:
    """Render a plain-text exact-backed mission summary."""

    lines = [
        "Exact-backed mission summary",
        f"mission_id: {summary.mission_id}",
        f"mission_path: {summary.mission_path}",
        f"benchmark_seed_count: {summary.benchmark_seed_count}",
    ]
    if summary.exact_artifact_dir is not None:
        lines.append(f"exact_artifact_dir: {summary.exact_artifact_dir}")
    lines.append(f"exact_artifact_has_action_values: {summary.exact_artifact_has_action_values}")
    if summary.exact_full_space_ceiling is not None:
        lines.append(f"exact_full_space_ceiling: {summary.exact_full_space_ceiling:.12f}")
    if summary.exact_equivalent_200 is not None:
        lines.append(f"exact_equivalent_200: {summary.exact_equivalent_200:.6f}")
    if summary.exact_fixed_seed_ceiling_wins is not None:
        lines.append(
            "exact_fixed_seed_ceiling: "
            f"{summary.exact_fixed_seed_ceiling_wins}/{summary.benchmark_seed_count}",
        )
    if summary.exact_fixed_seed_ceiling_ratio is not None:
        lines.append(
            "exact_fixed_seed_ceiling_ratio: "
            f"{summary.exact_fixed_seed_ceiling_ratio:.6f}",
        )
    if summary.exact_fixed_seed_source is not None:
        lines.append(f"exact_fixed_seed_source: {summary.exact_fixed_seed_source}")
    if summary.exact_fixed_seed_caveat is not None:
        lines.append(f"exact_fixed_seed_caveat: {summary.exact_fixed_seed_caveat}")

    if summary.policy_artifact_dir is not None:
        lines.append(f"policy_artifact_dir: {summary.policy_artifact_dir}")
    if summary.policy_agent_name is not None:
        lines.append(f"policy_agent_name: {summary.policy_agent_name}")
    if summary.policy_full_probability_value is not None:
        lines.append(f"policy_full_probability_value: {summary.policy_full_probability_value:.12f}")
    if summary.policy_equivalent_200 is not None:
        lines.append(f"policy_equivalent_200: {summary.policy_equivalent_200:.6f}")
    if summary.policy_vs_exact_ceiling_ratio is not None:
        lines.append(f"policy_vs_exact_ceiling_ratio: {summary.policy_vs_exact_ceiling_ratio:.6f}")
    if summary.policy_seed_wins is not None:
        lines.append(f"policy_seed_wins: {summary.policy_seed_wins}/{summary.benchmark_seed_count}")
    if summary.policy_seed_ratio is not None:
        lines.append(f"policy_seed_ratio: {summary.policy_seed_ratio:.6f}")
    if summary.policy_vs_seed_ceiling_ratio is not None:
        lines.append(f"policy_vs_seed_ceiling_ratio: {summary.policy_vs_seed_ceiling_ratio:.6f}")
    return "\n".join(lines)


__all__ = [
    "KNOWN_MISSION_EXACT_ANCHORS",
    "ExactFixedSeedSource",
    "KnownMissionExactAnchor",
    "MissionSummary",
    "benchmark_policy_seed_wins",
    "build_mission_summary",
    "deterministic_exact_seed_wins_from_artifact",
    "deterministic_exact_seed_wins_from_solver",
    "format_mission_summary_report",
]
