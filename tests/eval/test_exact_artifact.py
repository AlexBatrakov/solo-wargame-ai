from __future__ import annotations

from pathlib import Path

import pytest

from solo_wargame_ai.domain.resolver import get_legal_actions
from solo_wargame_ai.domain.state import create_initial_game_state
from solo_wargame_ai.eval import exact_artifact as exact_artifact_module
from solo_wargame_ai.io import load_mission

MISSION1_PATH = (
    Path(__file__).resolve().parents[2]
    / "configs"
    / "missions"
    / "mission_01_secure_the_woods_1.toml"
)


def _build_stub_exact_artifact(
    monkeypatch: pytest.MonkeyPatch,
    artifact_dir: Path,
) -> tuple[dict[str, object], bytes, tuple[object, ...]]:
    mission = load_mission(MISSION1_PATH)
    root_state = create_initial_game_state(mission, seed=0)
    legal_actions = tuple(get_legal_actions(root_state))
    assert len(legal_actions) == 2
    q_values = (0.6, 0.8)
    codec = exact_artifact_module.PackedPublicStateCodec(MISSION1_PATH)
    root_key = codec.pack_canonical(root_state)

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

    metadata = exact_artifact_module.build_exact_artifact(
        mission_path=MISSION1_PATH,
        artifact_dir=artifact_dir,
        progress_interval_sec=0.0,
        store_action_values=True,
    )
    return metadata, root_key, legal_actions


def test_build_exact_artifact_writes_generic_sqlite_and_metadata(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    artifact_dir = tmp_path / "exact-artifact"
    metadata, root_key, legal_actions = _build_stub_exact_artifact(
        monkeypatch,
        artifact_dir,
    )

    assert metadata["artifact_format"] == exact_artifact_module.EXACT_ARTIFACT_FORMAT
    assert metadata["mission_path"] == str(MISSION1_PATH)
    assert metadata["root_value"] == pytest.approx(0.8)
    assert metadata["stores_action_values"] is True
    assert metadata["action_value_row_count"] == 2

    stats = exact_artifact_module.read_exact_artifact_stats(artifact_dir)
    assert stats["root_value"] == pytest.approx(0.8)

    verification = exact_artifact_module.verify_exact_artifact(artifact_dir)
    assert verification.root_value_match is True
    assert verification.action_value_row_count == 2
    assert verification.stores_action_values is True

    artifact = exact_artifact_module.ExactArtifact(
        db_path=exact_artifact_module.resolve_exact_db_path(artifact_dir),
        metadata_path=artifact_dir / "metadata.json",
        mission_path=MISSION1_PATH,
    )
    try:
        rows = artifact.lookup_action_values_key(root_key)
        assert len(rows) == 2
        chosen_label, chosen_repr, chosen_q = artifact.lookup_exact_chosen_action_key(
            root_key,
        )
    finally:
        artifact.close()

    assert chosen_label == exact_artifact_module.action_label(legal_actions[1])
    assert chosen_repr == repr(legal_actions[1])
    assert chosen_q == pytest.approx(0.8)


def test_resolve_exact_db_path_accepts_single_legacy_sqlite(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "legacy-artifact"
    artifact_dir.mkdir()
    legacy_db = artifact_dir / "legacy.sqlite3"
    legacy_db.write_bytes(b"")

    assert exact_artifact_module.resolve_exact_db_path(artifact_dir) == legacy_db
