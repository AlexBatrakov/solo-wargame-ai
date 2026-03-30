from __future__ import annotations

import json

from solo_wargame_ai.cli import exact_guided_heuristic_comparison


class _FakeComparison:
    def to_payload(self) -> dict[str, object]:
        return {
            "comparison_kind": "exact_guided_heuristic_comparison",
            "mission2": {
                "promoted_summary": {
                    "policy_seed_wins": 94,
                    "policy_seed_ratio": 0.47,
                    "policy_vs_seed_ceiling_ratio": 94 / 131,
                },
            },
            "successor_progression_summary": [
                "HeuristicAgent remains the preserved historical baseline.",
            ],
        }


def test_cli_prints_report_and_writes_outputs(
    monkeypatch,
    tmp_path,
    capsys,
) -> None:
    comparison = _FakeComparison()
    seen_kwargs: dict[str, object] = {}

    def fake_build_exact_guided_heuristic_comparison(**kwargs):  # type: ignore[no-untyped-def]
        seen_kwargs.update(kwargs)
        return comparison

    def fake_format_exact_guided_heuristic_report(received_comparison) -> str:
        assert received_comparison is comparison
        return "comparison report"

    monkeypatch.setattr(
        exact_guided_heuristic_comparison,
        "build_exact_guided_heuristic_comparison",
        fake_build_exact_guided_heuristic_comparison,
    )
    monkeypatch.setattr(
        exact_guided_heuristic_comparison,
        "format_exact_guided_heuristic_report",
        fake_format_exact_guided_heuristic_report,
    )

    output_path = tmp_path / "reports" / "comparison.txt"
    json_output_path = tmp_path / "reports" / "comparison.json"

    exit_code = exact_guided_heuristic_comparison.main(
        [
            "--seed-stop",
            "200",
            "--mission1-exact-artifact-dir",
            str(tmp_path / "mission1-exact"),
            "--mission1-historical-policy-artifact-dir",
            str(tmp_path / "mission1-historical"),
            "--mission1-promoted-policy-artifact-dir",
            str(tmp_path / "mission1-promoted"),
            "--mission2-exact-artifact-dir",
            str(tmp_path / "mission2-exact"),
            "--output",
            str(output_path),
            "--json-output",
            str(json_output_path),
        ],
    )

    assert exit_code == 0
    assert seen_kwargs["seed_stop"] == 200
    assert seen_kwargs["mission1_exact_artifact_dir"] == tmp_path / "mission1-exact"
    assert seen_kwargs["mission1_historical_policy_artifact_dir"] == (
        tmp_path / "mission1-historical"
    )
    assert seen_kwargs["mission1_promoted_policy_artifact_dir"] == (
        tmp_path / "mission1-promoted"
    )
    assert seen_kwargs["mission2_exact_artifact_dir"] == tmp_path / "mission2-exact"
    assert capsys.readouterr().out == "comparison report\n"
    assert output_path.read_text(encoding="utf-8") == "comparison report\n"

    payload = json.loads(json_output_path.read_text(encoding="utf-8"))
    assert payload["comparison_kind"] == "exact_guided_heuristic_comparison"
    assert payload["mission2"]["promoted_summary"]["policy_seed_wins"] == 94
    assert payload["mission2"]["promoted_summary"]["policy_seed_ratio"] == 0.47
