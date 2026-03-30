"""Generic exact-artifact build/read/verify workflow for exact-solved missions."""

from __future__ import annotations

import json
import sqlite3
import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from solo_wargame_ai.domain.actions import GameAction
from solo_wargame_ai.domain.state import GameState, create_initial_game_state
from solo_wargame_ai.io import load_mission

from .exact_policy_solver import (
    EXACT_TIE_TOLERANCE_DEFAULT,
    PackedPublicStateCodec,
    action_label,
    build_capped_exact_policy_solver,
)

DEFAULT_ARTIFACT_ROOT = Path(".project_local/artifacts")
EXACT_ARTIFACT_FORMAT = "sqlite_blob_keyed_exact_nonterminal_values_v1"


@dataclass(frozen=True, slots=True)
class ExactActionValueRow:
    action_label: str
    action_repr: str
    q_star: float
    is_optimal: int


@dataclass(frozen=True, slots=True)
class ExactArtifactVerificationResult:
    artifact_dir: Path
    mission_id: str
    mission_path: Path
    root_value_metadata: float
    root_value_lookup: float | None
    root_value_match: bool
    stored_row_count: int
    action_value_row_count: int
    stores_action_values: bool
    exact_tie_break_rule: str | None
    exact_tie_tolerance: float | None
    db_size_mb: float
    artifact_format: str
    key_codec_version: str
    uses_british_swap_symmetry: bool | None

    def to_payload(self) -> dict[str, object]:
        return {
            "artifact_dir": str(self.artifact_dir),
            "mission_id": self.mission_id,
            "mission_path": str(self.mission_path),
            "root_value_metadata": self.root_value_metadata,
            "root_value_lookup": self.root_value_lookup,
            "root_value_match": self.root_value_match,
            "stored_row_count": self.stored_row_count,
            "action_value_row_count": self.action_value_row_count,
            "stores_action_values": self.stores_action_values,
            "exact_tie_break_rule": self.exact_tie_break_rule,
            "exact_tie_tolerance": self.exact_tie_tolerance,
            "db_size_mb": self.db_size_mb,
            "artifact_format": self.artifact_format,
            "key_codec_version": self.key_codec_version,
            "uses_british_swap_symmetry": self.uses_british_swap_symmetry,
        }


def default_exact_artifact_dir(mission_path: Path) -> Path:
    """Return the default local artifact directory for a mission."""

    mission = load_mission(mission_path)
    return DEFAULT_ARTIFACT_ROOT / f"{mission.mission_id}_exact_artifact"


def resolve_exact_db_path(artifact_dir: Path) -> Path:
    """Resolve the exact-artifact SQLite path, keeping legacy layout compatibility."""

    generic = artifact_dir / "exact_values.sqlite3"
    if generic.exists():
        return generic
    legacy_candidates = sorted(artifact_dir.glob("*.sqlite3"))
    if len(legacy_candidates) == 1:
        return legacy_candidates[0]
    return generic


class ExactArtifact:
    """Readonly lookup over a mission exact artifact."""

    def __init__(
        self,
        *,
        db_path: Path,
        metadata_path: Path,
        mission_path: Path | None = None,
    ) -> None:
        self.db_path = Path(db_path)
        self.metadata_path = Path(metadata_path)
        self.metadata = json.loads(self.metadata_path.read_text())
        if mission_path is None:
            mission_path = Path(self.metadata["mission_path"])
        self.codec = PackedPublicStateCodec(Path(mission_path))
        self.connection = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)

    def lookup_key(self, key: bytes) -> float | None:
        row = self.connection.execute(
            "SELECT value FROM states WHERE key = ?",
            (sqlite3.Binary(key),),
        ).fetchone()
        return None if row is None else float(row[0])

    def lookup_value(self, state: GameState) -> float | None:
        return self.lookup_key(self.codec.pack_canonical(state))

    def has_action_values(self) -> bool:
        row = self.connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'action_values'",
        ).fetchone()
        return row is not None

    def lookup_action_values_key(self, key: bytes) -> tuple[ExactActionValueRow, ...]:
        if not self.has_action_values():
            return ()
        rows = self.connection.execute(
            "SELECT action_label, action_repr, q_star, is_optimal "
            "FROM action_values "
            "WHERE key = ? "
            "ORDER BY action_label ASC, action_repr ASC",
            (sqlite3.Binary(key),),
        ).fetchall()
        return tuple(
            ExactActionValueRow(
                action_label=str(action_label_text),
                action_repr=str(action_repr_text),
                q_star=float(q_star),
                is_optimal=int(is_optimal),
            )
            for action_label_text, action_repr_text, q_star, is_optimal in rows
        )

    def lookup_action_values(self, state: GameState) -> tuple[ExactActionValueRow, ...]:
        return self.lookup_action_values_key(self.codec.pack_canonical(state))

    def lookup_exact_chosen_action_key(
        self,
        key: bytes,
        *,
        tolerance: float | None = None,
    ) -> tuple[str, str, float] | None:
        rows = self.lookup_action_values_key(key)
        if not rows:
            return None
        if tolerance is None:
            tolerance = float(
                self.metadata.get("exact_tie_tolerance", EXACT_TIE_TOLERANCE_DEFAULT),
            )
        best_value = max(row.q_star for row in rows)
        best_rows = [
            (row.action_label, row.action_repr, row.q_star)
            for row in rows
            if best_value - row.q_star <= tolerance
        ]
        return min(best_rows, key=lambda row: (row[0], row[1]))

    def close(self) -> None:
        self.connection.close()


class SqliteExactArtifactSink:
    """Incremental SQLite writer for solved exact values."""

    def __init__(
        self,
        *,
        db_path: Path,
        insert_batch_size: int,
        progress_interval_sec: float,
        store_action_values: bool,
    ) -> None:
        self.db_path = Path(db_path)
        self.insert_batch_size = insert_batch_size
        self.progress_interval_sec = progress_interval_sec
        self.store_action_values = store_action_values
        self.connection = sqlite3.connect(self.db_path)
        self.connection.execute("PRAGMA journal_mode=OFF")
        self.connection.execute("PRAGMA synchronous=OFF")
        self.connection.execute("PRAGMA temp_store=MEMORY")
        self.connection.execute("PRAGMA cache_size=-200000")
        self.connection.execute("PRAGMA locking_mode=EXCLUSIVE")
        self.connection.execute("PRAGMA page_size=32768")
        self.connection.execute(
            "CREATE TABLE states ( key BLOB PRIMARY KEY, value REAL NOT NULL) WITHOUT ROWID",
        )
        if self.store_action_values:
            self.connection.execute(
                "CREATE TABLE action_values ("
                " key BLOB NOT NULL,"
                " action_label TEXT NOT NULL,"
                " action_repr TEXT NOT NULL,"
                " q_star REAL NOT NULL,"
                " is_optimal INTEGER NOT NULL,"
                " PRIMARY KEY (key, action_label, action_repr)"
                ") WITHOUT ROWID",
            )
        self.pending: list[tuple[sqlite3.Binary, float]] = []
        self.pending_actions: list[tuple[sqlite3.Binary, str, str, float, int]] = []
        self.attempted = 0
        self.inserted = 0
        self.attempted_actions = 0
        self.inserted_actions = 0
        self.states_with_action_values = 0
        self.key_length_min: int | None = None
        self.key_length_max: int | None = None
        self.started = time.monotonic()
        self.last_report = self.started

    def add(self, key: bytes, value: float) -> None:
        self.attempted += 1
        key_len = len(key)
        if self.key_length_min is None or key_len < self.key_length_min:
            self.key_length_min = key_len
        if self.key_length_max is None or key_len > self.key_length_max:
            self.key_length_max = key_len
        self.pending.append((sqlite3.Binary(key), value))
        if len(self.pending) >= self.insert_batch_size:
            self.flush()

    def add_action_values(
        self,
        key: bytes,
        rows: Sequence[tuple[str, str, float, int]],
    ) -> None:
        if not self.store_action_values or not rows:
            return
        self.states_with_action_values += 1
        key_blob = sqlite3.Binary(key)
        for action_label_text, action_repr_text, q_star, is_optimal in rows:
            self.attempted_actions += 1
            self.pending_actions.append(
                (key_blob, action_label_text, action_repr_text, q_star, is_optimal),
            )
        if len(self.pending_actions) >= self.insert_batch_size:
            self.flush()

    def flush(self, *, force: bool = False) -> None:
        if not self.pending and not self.pending_actions:
            return
        with self.connection:
            if self.pending:
                before = self.connection.total_changes
                self.connection.executemany(
                    "INSERT OR IGNORE INTO states(key, value) VALUES (?, ?)",
                    self.pending,
                )
                self.inserted += self.connection.total_changes - before
                self.pending.clear()
            if self.pending_actions:
                before = self.connection.total_changes
                self.connection.executemany(
                    "INSERT OR IGNORE INTO action_values("
                    "key, action_label, action_repr, q_star, is_optimal"
                    ") VALUES (?, ?, ?, ?, ?)",
                    self.pending_actions,
                )
                self.inserted_actions += self.connection.total_changes - before
                self.pending_actions.clear()
        now = time.monotonic()
        if force or now - self.last_report >= self.progress_interval_sec:
            print(
                "[artifact] "
                f"attempted={self.attempted} "
                f"inserted={self.inserted} "
                f"attempted_actions={self.attempted_actions} "
                f"inserted_actions={self.inserted_actions} "
                f"elapsed={now - self.started:.1f}s",
                flush=True,
            )
            self.last_report = now

    def close(self) -> None:
        self.flush(force=True)
        self.connection.close()


def build_exact_artifact(
    *,
    mission_path: Path,
    artifact_dir: Path | None = None,
    progress_interval_sec: float = 30.0,
    insert_batch_size: int = 20_000,
    cap_metric: str = "auto",
    memory_cap_gb: float = 20.0,
    memory_low_water_gb: float = 17.0,
    trim_check_interval: int = 2048,
    min_trim_entries: int = 8192,
    cache_through_turn: int | None = None,
    overwrite: bool = False,
    store_action_values: bool = False,
    exact_tie_tolerance: float = EXACT_TIE_TOLERANCE_DEFAULT,
) -> dict[str, object]:
    """Build an exact-value artifact and return its metadata payload."""

    mission_path = Path(mission_path)
    mission = load_mission(mission_path)
    artifact_dir = (
        Path(artifact_dir) if artifact_dir is not None else default_exact_artifact_dir(mission_path)
    )
    artifact_dir.mkdir(parents=True, exist_ok=True)
    db_path = artifact_dir / "exact_values.sqlite3"
    metadata_path = artifact_dir / "metadata.json"
    tmp_db_path = artifact_dir / "exact_values.tmp.sqlite3"
    tmp_metadata_path = artifact_dir / "metadata.tmp.json"

    if not overwrite and (db_path.exists() or metadata_path.exists()):
        raise FileExistsError(
            f"artifact already exists at {artifact_dir}; pass overwrite=True to rebuild",
        )

    for path in (tmp_db_path, tmp_metadata_path):
        if path.exists():
            path.unlink()

    codec = PackedPublicStateCodec(mission_path)
    sink = SqliteExactArtifactSink(
        db_path=tmp_db_path,
        insert_batch_size=insert_batch_size,
        progress_interval_sec=progress_interval_sec,
        store_action_values=store_action_values,
    )
    build_started = time.monotonic()

    def on_state_solved(
        state: GameState,
        key: bytes,
        _value: float,
        q_entries: list[tuple[GameAction, float]] | None,
    ) -> None:
        if not q_entries or len(q_entries) <= 1 or not store_action_values:
            return
        best_q = max(q_star for _action, q_star in q_entries)
        rows = [
            (
                action_label(action),
                repr(action),
                q_star,
                1 if best_q - q_star <= exact_tie_tolerance else 0,
            )
            for action, q_star in q_entries
        ]
        sink.add_action_values(key, rows)

    solver = build_capped_exact_policy_solver(
        mission_path=mission_path,
        progress_interval_sec=progress_interval_sec,
        cap_metric=cap_metric,
        memory_cap_gb=memory_cap_gb,
        memory_low_water_gb=memory_low_water_gb,
        trim_check_interval=trim_check_interval,
        min_trim_entries=min_trim_entries,
        cache_through_turn=cache_through_turn,
        on_state_solved=on_state_solved if store_action_values else None,
    )

    original_put = solver.cache.put

    def exporting_put(turn: int, progress_bucket: int, key: bytes, value: float) -> None:
        sink.add(key, value)
        original_put(turn, progress_bucket, key, value)

    solver.cache.put = exporting_put  # type: ignore[method-assign]

    try:
        root_state = create_initial_game_state(mission, seed=0)
        root_value = solver.value(root_state)
        solver.maybe_report_progress(force=True)
        sink.close()
    finally:
        if sink.connection:
            try:
                sink.connection.close()
            except Exception:
                pass

    check_connection = sqlite3.connect(tmp_db_path)
    try:
        row_count = int(check_connection.execute("SELECT COUNT(*) FROM states").fetchone()[0])
        action_row_count = (
            int(check_connection.execute("SELECT COUNT(*) FROM action_values").fetchone()[0])
            if store_action_values
            else 0
        )
    finally:
        check_connection.close()

    db_size_bytes = tmp_db_path.stat().st_size
    metadata = {
        **codec.metadata(),
        "artifact_format": EXACT_ARTIFACT_FORMAT,
        "mission_id": mission.mission_id,
        "mission_path": str(mission_path),
        "built_at_epoch_sec": time.time(),
        "root_value": root_value,
        "stored_row_count": row_count,
        "db_size_bytes": int(db_size_bytes),
        "db_size_mb": round(db_size_bytes / (1024 * 1024), 3),
        "key_length_min_bytes": sink.key_length_min,
        "key_length_max_bytes": sink.key_length_max,
        "attempted_store_count": int(sink.attempted),
        "inserted_store_count": int(sink.inserted),
        "stores_action_values": bool(store_action_values),
        "exact_tie_tolerance": float(exact_tie_tolerance),
        "exact_tie_break_rule": (
            "maximize q_star; among ties within tolerance choose smallest "
            "(action_label, action_repr)"
        ),
        "action_value_row_count": int(action_row_count),
        "attempted_action_store_count": int(sink.attempted_actions),
        "inserted_action_store_count": int(sink.inserted_actions),
        "states_with_action_values": int(sink.states_with_action_values),
        "progress_interval_sec": progress_interval_sec,
        "insert_batch_size": insert_batch_size,
        "cap_metric": cap_metric,
        "memory_cap_gb": memory_cap_gb,
        "memory_low_water_gb": memory_low_water_gb,
        "trim_check_interval": trim_check_interval,
        "min_trim_entries": min_trim_entries,
        "cache_through_turn": cache_through_turn,
        "build_elapsed_sec": round(time.monotonic() - build_started, 3),
        "stores_observed": int(solver.cache.stores),
        "evictions_observed": int(solver.cache.evictions),
        "trims_observed": int(solver.cache.trims),
    }

    tmp_metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n")
    if db_path.exists():
        db_path.unlink()
    if metadata_path.exists():
        metadata_path.unlink()
    tmp_db_path.replace(db_path)
    tmp_metadata_path.replace(metadata_path)
    return metadata


def read_exact_artifact_stats(artifact_dir: Path) -> dict[str, object]:
    """Read exact-artifact metadata."""

    return json.loads((Path(artifact_dir) / "metadata.json").read_text())


def verify_exact_artifact(artifact_dir: Path) -> ExactArtifactVerificationResult:
    """Verify that an exact artifact root lookup matches metadata."""

    artifact_dir = Path(artifact_dir)
    metadata = read_exact_artifact_stats(artifact_dir)
    mission_path = Path(str(metadata["mission_path"]))
    mission = load_mission(mission_path)
    root_state = create_initial_game_state(mission, seed=0)
    artifact = ExactArtifact(
        db_path=resolve_exact_db_path(artifact_dir),
        metadata_path=artifact_dir / "metadata.json",
        mission_path=mission_path,
    )
    try:
        root_lookup = artifact.lookup_value(root_state)
    finally:
        artifact.close()

    return ExactArtifactVerificationResult(
        artifact_dir=artifact_dir,
        mission_id=str(metadata["mission_id"]),
        mission_path=mission_path,
        root_value_metadata=float(metadata["root_value"]),
        root_value_lookup=root_lookup,
        root_value_match=root_lookup == metadata["root_value"],
        stored_row_count=int(metadata["stored_row_count"]),
        action_value_row_count=int(metadata.get("action_value_row_count", 0)),
        stores_action_values=bool(metadata.get("stores_action_values", False)),
        exact_tie_break_rule=metadata.get("exact_tie_break_rule"),
        exact_tie_tolerance=(
            float(metadata["exact_tie_tolerance"])
            if metadata.get("exact_tie_tolerance") is not None
            else None
        ),
        db_size_mb=float(metadata["db_size_mb"]),
        artifact_format=str(metadata["artifact_format"]),
        key_codec_version=str(metadata["key_codec_version"]),
        uses_british_swap_symmetry=metadata.get("uses_british_swap_symmetry"),
    )


__all__ = [
    "DEFAULT_ARTIFACT_ROOT",
    "EXACT_ARTIFACT_FORMAT",
    "ExactActionValueRow",
    "ExactArtifact",
    "ExactArtifactVerificationResult",
    "SqliteExactArtifactSink",
    "build_exact_artifact",
    "default_exact_artifact_dir",
    "read_exact_artifact_stats",
    "resolve_exact_db_path",
    "verify_exact_artifact",
]
