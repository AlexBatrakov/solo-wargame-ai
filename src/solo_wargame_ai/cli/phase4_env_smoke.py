"""Thin manual entrypoint for accepted Phase 4 Mission 1 env smoke reruns."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from solo_wargame_ai.env import Mission1Env
from solo_wargame_ai.io.mission_loader import load_mission

MISSION_PATH = (
    Path(__file__).resolve().parents[3]
    / "configs"
    / "missions"
    / "mission_01_secure_the_woods_1.toml"
)


@dataclass(frozen=True, slots=True)
class SmokeEpisodeSummary:
    """Compact summary for one completed deterministic Mission 1 smoke run."""

    seed: int
    action_catalog_size: int
    decision_steps: int
    terminated: bool
    truncated: bool
    terminal_outcome: str | None
    final_reward: float


def build_parser() -> argparse.ArgumentParser:
    """Build the tiny operator surface for one Mission 1 env smoke run."""

    parser = argparse.ArgumentParser(
        description=(
            "Run one deterministic Mission 1 env smoke episode using "
            "first-legal-action selection."
        ),
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Seed passed to Mission1Env.reset(seed=...). Defaults to 0.",
    )
    return parser


def run_smoke_episode(*, seed: int) -> SmokeEpisodeSummary:
    """Run one deterministic Mission 1 episode by always taking the first legal id."""

    mission = load_mission(MISSION_PATH)
    env = Mission1Env(mission)
    _, info = env.reset(seed=seed)
    terminated = False
    truncated = False
    reward = 0.0

    while not (terminated or truncated):
        legal_action_ids = info["legal_action_ids"]
        if not legal_action_ids:
            raise RuntimeError(
                "Phase 4 env smoke reached a nonterminal state without legal actions",
            )
        _, reward, terminated, truncated, info = env.step(legal_action_ids[0])

    return SmokeEpisodeSummary(
        seed=seed,
        action_catalog_size=env.action_space_size,
        decision_steps=info["decision_step_count"],
        terminated=terminated,
        truncated=truncated,
        terminal_outcome=info["terminal_outcome"],
        final_reward=reward,
    )


def format_phase4_report(summary: SmokeEpisodeSummary) -> str:
    """Render the accepted one-episode operator summary."""

    lines = [
        "Phase 4 env smoke",
        f"mission: {MISSION_PATH.name}",
        "policy: first_legal_action",
        f"seed: {summary.seed}",
        f"action_catalog_size: {summary.action_catalog_size}",
        f"decision_steps: {summary.decision_steps}",
        f"terminated: {summary.terminated}",
        f"truncated: {summary.truncated}",
        f"terminal_outcome: {summary.terminal_outcome}",
        f"final_reward: {summary.final_reward:+.1f}",
    ]
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the accepted thin Phase 4 env smoke surface."""

    args = build_parser().parse_args(argv)
    summary = run_smoke_episode(seed=args.seed)
    print(format_phase4_report(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
