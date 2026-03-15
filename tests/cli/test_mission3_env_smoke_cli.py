from __future__ import annotations

from pathlib import Path

from solo_wargame_ai.cli import mission3_env_smoke


def test_main_prints_a_completed_mission3_env_smoke_summary(
    monkeypatch,
    capsys,
) -> None:
    mission = object()

    class FakeEnv:
        def __init__(self, received_mission: object) -> None:
            assert received_mission is mission
            self.action_space_size = 49
            self._step_calls = 0

        def reset(self, *, seed: int):
            assert seed == 7
            return {}, {
                "legal_action_ids": [2, 4],
                "decision_step_count": 0,
                "terminal_outcome": None,
            }

        def step(self, action_id: int):
            self._step_calls += 1
            if self._step_calls == 1:
                assert action_id == 2
                return {}, 0.0, False, False, {
                    "legal_action_ids": [12],
                    "decision_step_count": 1,
                    "terminal_outcome": None,
                }

            assert action_id == 12
            return {"terminal_outcome": "victory"}, 1.0, True, False, {
                "legal_action_ids": [],
                "decision_step_count": 2,
                "terminal_outcome": "victory",
            }

    def fake_load_mission(path: Path) -> object:
        assert path == mission3_env_smoke.MISSION_PATH
        return mission

    monkeypatch.setattr(mission3_env_smoke, "load_mission", fake_load_mission)
    monkeypatch.setattr(mission3_env_smoke, "Mission3Env", FakeEnv)

    exit_code = mission3_env_smoke.main(["--seed", "7"])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "Mission 3 env smoke" in output
    assert "policy: first_legal_action" in output
    assert "seed: 7" in output
    assert "action_catalog_size: 49" in output
    assert "decision_steps: 2" in output
    assert "terminated: True" in output
    assert "truncated: False" in output
    assert "terminal_outcome: victory" in output
    assert "final_reward: +1.0" in output
    assert "wrapper_surface: mission3_env" in output
    assert "historical_comparison_surface: preserved separately" in output
    assert "qm_" not in output
