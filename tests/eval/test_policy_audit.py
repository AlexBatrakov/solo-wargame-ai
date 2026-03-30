from __future__ import annotations

from pathlib import Path

import pytest

from solo_wargame_ai.domain.resolver import get_legal_actions
from solo_wargame_ai.domain.state import create_initial_game_state
from solo_wargame_ai.eval import exact_artifact as exact_artifact_module
from solo_wargame_ai.eval import policy_audit as policy_audit_module
from solo_wargame_ai.eval.exact_policy_solver import action_label
from solo_wargame_ai.io import load_mission

MISSION1_PATH = (
    Path(__file__).resolve().parents[2]
    / "configs"
    / "missions"
    / "mission_01_secure_the_woods_1.toml"
)


def _build_root_exact_artifact(
    monkeypatch: pytest.MonkeyPatch,
    artifact_dir: Path,
) -> tuple[bytes, tuple[object, ...]]:
    mission = load_mission(MISSION1_PATH)
    root_state = create_initial_game_state(mission, seed=0)
    legal_actions = tuple(get_legal_actions(root_state))
    assert len(legal_actions) == 2
    q_values = (0.6, 0.8)
    codec = exact_artifact_module.PackedPublicStateCodec(MISSION1_PATH)

    class FakeCache:
        def __init__(self) -> None:
            self.stores = 0
            self.evictions = 0
            self.trims = 0

        def put(
            self,
            _turn: int,
            _progress_bucket: int,
            _key: bytes,
            _value: float,
        ) -> None:
            self.stores += 1

    class FakeSolver:
        def __init__(self, on_state_solved) -> None:  # type: ignore[no-untyped-def]
            self.cache = FakeCache()
            self._on_state_solved = on_state_solved

        def value(self, state) -> float:  # type: ignore[no-untyped-def]
            key = codec.pack_canonical(state)
            self.cache.put(state.turn, 0, key, max(q_values))
            if self._on_state_solved is not None:
                self._on_state_solved(
                    state,
                    key,
                    max(q_values),
                    list(zip(legal_actions, q_values, strict=True)),
                )
            return max(q_values)

        def maybe_report_progress(self, *, force: bool = False) -> None:
            del force

    def fake_build_capped_exact_policy_solver(  # type: ignore[no-untyped-def]
        *,
        mission_path: Path,
        on_state_solved=None,
        **_kwargs,
    ):
        assert Path(mission_path) == MISSION1_PATH
        return FakeSolver(on_state_solved)

    monkeypatch.setattr(
        exact_artifact_module,
        "build_capped_exact_policy_solver",
        fake_build_capped_exact_policy_solver,
    )
    exact_artifact_module.build_exact_artifact(
        mission_path=MISSION1_PATH,
        artifact_dir=artifact_dir,
        progress_interval_sec=0.0,
        store_action_values=True,
    )
    return codec.pack_canonical(root_state), legal_actions


def test_build_policy_audit_artifact_writes_generic_sqlite_and_metadata(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    exact_artifact_dir = tmp_path / "exact-artifact"
    root_key, legal_actions = _build_root_exact_artifact(
        monkeypatch,
        exact_artifact_dir,
    )

    class StubAgent:
        name = "stub-policy"

        def select_action(self, _state, legal_actions):  # type: ignore[no-untyped-def]
            return legal_actions[0]

    class FakeCache:
        def __init__(self) -> None:
            self.stores = 0
            self.evictions = 0
            self.trims = 0

        def get(
            self,
            _turn: int,
            _progress_bucket: int,
            _key: bytes,
        ) -> float | None:
            return None

    class FakePolicySolver:
        def __init__(self) -> None:
            self.cache = FakeCache()

        def normalize_state(self, state):  # type: ignore[no-untyped-def]
            mission = load_mission(MISSION1_PATH)
            codec = exact_artifact_module.PackedPublicStateCodec(MISSION1_PATH)
            return state, codec.pack_canonical(
                create_initial_game_state(mission, seed=0),
            )

        def value(self, _state) -> float:  # type: ignore[no-untyped-def]
            return 0.8

        def build_policy_engine(self, pick_action):  # type: ignore[no-untyped-def]
            def choose_action_for_state(state, _key):  # type: ignore[no-untyped-def]
                return pick_action(state, tuple(get_legal_actions(state)))

            def H(_state) -> float:  # type: ignore[no-untyped-def]
                return 0.4

            def policy_q_value_impl(state, action) -> float:  # type: ignore[no-untyped-def]
                chosen = choose_action_for_state(state, root_key)
                return 0.4 if action == chosen else 0.25

            def policy_successors(state):  # type: ignore[no-untyped-def]
                chosen = choose_action_for_state(state, root_key)
                return state, root_key, chosen, ()

            def maybe_report_policy_progress(*, force: bool = False) -> None:
                del force

            return (
                H,
                policy_q_value_impl,
                choose_action_for_state,
                policy_successors,
                maybe_report_policy_progress,
            )

    def fake_build_capped_exact_policy_solver(  # type: ignore[no-untyped-def]
        *,
        mission_path: Path,
        **_kwargs,
    ):
        assert Path(mission_path) == MISSION1_PATH
        return FakePolicySolver()

    monkeypatch.setattr(
        policy_audit_module,
        "build_capped_exact_policy_solver",
        fake_build_capped_exact_policy_solver,
    )

    artifact_dir = tmp_path / "policy-audit"
    metadata = policy_audit_module.build_policy_audit_artifact(
        mission_path=MISSION1_PATH,
        exact_artifact_dir=exact_artifact_dir,
        build_agent=StubAgent,
        agent_name="stub-policy",
        artifact_dir=artifact_dir,
        progress_interval_sec=0.0,
        store_action_values=True,
    )

    assert metadata["artifact_format"] == policy_audit_module.POLICY_AUDIT_ARTIFACT_FORMAT
    assert metadata["policy_root_value"] == pytest.approx(0.4)
    assert metadata["state_row_count"] == 1
    assert metadata["decision_summary_count"] == 1
    assert metadata["action_value_row_count"] == 2
    assert metadata["exact_action_values_reused"] is True

    artifact = policy_audit_module.PolicyAuditArtifact(artifact_dir=artifact_dir)
    try:
        root_row = artifact.lookup_state_row_key(root_key)
    finally:
        artifact.close()

    assert root_row is not None
    assert root_row.value_pi == pytest.approx(0.4)
    assert root_row.value_star == pytest.approx(0.8)
    assert root_row.chosen_q_star == pytest.approx(0.6)
    assert root_row.local_exact_regret == pytest.approx(0.2)
    assert root_row.chosen_action_label == action_label(legal_actions[0])

    verification = policy_audit_module.verify_policy_audit_artifact(artifact_dir)
    assert verification.policy_root_value_match is True
    assert verification.exact_action_values_reused is True
