"""Mission-1-local reporting helpers for the exact fair reference workflow."""

from __future__ import annotations

from typing import Any

from .mission1_exact_fair_ceiling import (
    Mission1ExactFairSmokeResult,
    Mission1ExactFairSolveResult,
)

MISSION1_EXACT_REFERENCE_KIND = "mission1_exact_fair_ceiling"
MISSION1_EXACT_REFERENCE_QUALIFICATION = (
    "Mission 1 exact fair-ceiling reference over player-visible information plus "
    "explicit rule knowledge."
)
MISSION1_PRESERVED_ANCHOR_QUALIFICATION = (
    "Preserved Mission 1 anchors remain separate historical references; "
    "RolloutSearchAgent 195/200 stays an oracle/planner-like reference rather "
    "than the fair target."
)
MISSION1_EXACT_REFERENCE_CLI_MODULE = "solo_wargame_ai.cli.mission1_exact_fair_reference"

Mission1ExactFairReferenceResult = Mission1ExactFairSmokeResult | Mission1ExactFairSolveResult


def format_mission1_exact_fair_reference_report(
    result: Mission1ExactFairReferenceResult,
    *,
    cli_module: str = MISSION1_EXACT_REFERENCE_CLI_MODULE,
) -> str:
    """Render the Mission 1 exact fair-reference report/operator handoff."""

    lines = [
        "Mission 1 exact fair reference",
        f"mode: {result.mode}",
        f"mission_id: {result.mission_id}",
        f"reference_kind: {MISSION1_EXACT_REFERENCE_KIND}",
        f"reference_status: {_reference_status(result)}",
        f"exact_reference_qualification: {MISSION1_EXACT_REFERENCE_QUALIFICATION}",
        f"preserved_anchor_qualification: {MISSION1_PRESERVED_ANCHOR_QUALIFICATION}",
        "",
    ]

    if isinstance(result, Mission1ExactFairSmokeResult):
        lines.extend(
            (
                "Smoke probe summary:",
                f"root_action_count: {result.root_action_count}",
                f"first_root_action: {result.first_root_action}",
                (
                    "first_root_action_outcome_mass: "
                    f"{result.first_root_action_outcome_mass:.12f}"
                ),
                (
                    "activation_roll_probability_mass: "
                    f"{result.chance_tables.activation_roll_probability_mass:.12f}"
                ),
                (
                    "reveal_probability_mass: "
                    f"{result.chance_tables.reveal_probability_mass:.12f}"
                ),
                f"interned_states: {result.solved_state_count}",
                "",
            ),
        )
    else:
        lines.extend(
            (
                "Exact fair reference result:",
                f"fair_ceiling: {result.fair_ceiling:.12f}",
                f"interned_states: {result.solved_state_count}",
                "root_actions:",
                *[
                    f"  {action}: {value:.12f}"
                    for action, value in result.root_action_values
                ],
                "",
            ),
        )

    lines.extend(
        (
            "Fair-agent contract:",
            *[f"  - {line}" for line in result.fair_agent_contract],
            "",
            "Preserved historical Mission 1 anchors:",
            *[f"  - {anchor}" for anchor in result.preserved_anchors],
            "",
            "Scratch estimate handling:",
            f"scratch_estimate_evidence_only: {result.scratch_estimate_evidence_only:.12f}",
            "scratch_estimate_status: evidence-only (not accepted reference)",
            "",
            "Operator handoff:",
            "substantive_exact_solve_owner: operator",
            "smoke_default: yes",
            f"smoke_command: {_cli_command(cli_module, mode='smoke')}",
            f"exact_solve_command: {_cli_command(cli_module, mode='exact')}",
            (
                "artifact_preservation: add --output <report-path> and "
                "--json-output <json-path> to preserve the exact fair reference "
                "separately from preserved historical anchors"
            ),
            "preserved_seeded_rerun_owner: operator",
        ),
    )
    return "\n".join(lines)


def mission1_exact_fair_reference_payload(
    result: Mission1ExactFairReferenceResult,
    *,
    cli_module: str = MISSION1_EXACT_REFERENCE_CLI_MODULE,
) -> dict[str, Any]:
    """Build a machine-readable Mission 1 exact fair-reference payload."""

    payload: dict[str, Any] = {
        "mission_id": result.mission_id,
        "mode": result.mode,
        "reference_kind": MISSION1_EXACT_REFERENCE_KIND,
        "reference_status": _reference_status(result),
        "exact_reference_qualification": MISSION1_EXACT_REFERENCE_QUALIFICATION,
        "preserved_anchor_qualification": MISSION1_PRESERVED_ANCHOR_QUALIFICATION,
        "fair_agent_contract": list(result.fair_agent_contract),
        "preserved_historical_anchors": list(result.preserved_anchors),
        "scratch_estimate_evidence_only": result.scratch_estimate_evidence_only,
        "scratch_estimate_status": "evidence_only_not_accepted_reference",
        "operator_handoff": {
            "substantive_exact_solve_owner": "operator",
            "smoke_default": True,
            "smoke_command": _cli_command(cli_module, mode="smoke"),
            "exact_solve_command": _cli_command(cli_module, mode="exact"),
            "artifact_preservation": (
                "add --output <report-path> and --json-output <json-path> to "
                "preserve the exact fair reference separately from preserved "
                "historical anchors"
            ),
            "preserved_seeded_rerun_owner": "operator",
        },
    }
    if isinstance(result, Mission1ExactFairSmokeResult):
        payload["smoke_probe"] = {
            "root_action_count": result.root_action_count,
            "first_root_action": result.first_root_action,
            "first_root_action_outcome_mass": result.first_root_action_outcome_mass,
            "activation_roll_probability_mass": (
                result.chance_tables.activation_roll_probability_mass
            ),
            "reveal_probability_mass": result.chance_tables.reveal_probability_mass,
            "interned_states": result.solved_state_count,
        }
        return payload

    payload["exact_result"] = {
        "fair_ceiling": result.fair_ceiling,
        "interned_states": result.solved_state_count,
        "root_action_values": [
            {"action": action, "value": value}
            for action, value in result.root_action_values
        ],
    }
    return payload


def _reference_status(result: Mission1ExactFairReferenceResult) -> str:
    if isinstance(result, Mission1ExactFairSmokeResult):
        return "smoke_probe_only"
    return "operator_run_exact_reference"


def _cli_command(cli_module: str, *, mode: str) -> str:
    return f".venv/bin/python -m {cli_module} --mode {mode}"


__all__ = [
    "MISSION1_EXACT_REFERENCE_CLI_MODULE",
    "MISSION1_EXACT_REFERENCE_KIND",
    "MISSION1_EXACT_REFERENCE_QUALIFICATION",
    "MISSION1_PRESERVED_ANCHOR_QUALIFICATION",
    "format_mission1_exact_fair_reference_report",
    "mission1_exact_fair_reference_payload",
]
