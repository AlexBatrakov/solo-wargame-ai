"""Generic fixed-policy audit artifact workflow."""

from __future__ import annotations

import json
import sqlite3
import time
from collections import Counter, deque
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from solo_wargame_ai.agents.base import Agent
from solo_wargame_ai.domain.actions import GameAction
from solo_wargame_ai.domain.legal_actions import lookup_orders_chart_row
from solo_wargame_ai.domain.resolver import get_legal_actions as resolver_legal_actions
from solo_wargame_ai.domain.state import GameState, TerminalOutcome, create_initial_game_state
from solo_wargame_ai.domain.units import BritishMorale, GermanUnitStatus
from solo_wargame_ai.io import load_mission

from .exact_artifact import ExactArtifact, default_exact_artifact_dir, resolve_exact_db_path
from .exact_policy_solver import (
    EXACT_TIE_TOLERANCE_DEFAULT,
    action_label,
    build_capped_exact_policy_solver,
)

POLICY_AUDIT_ARTIFACT_FORMAT = "sqlite_blob_keyed_policy_audit_v1"


def active_german_count(state: GameState) -> int:
    return sum(
        1 for unit in state.german_units.values() if unit.status is GermanUnitStatus.ACTIVE
    )


def low_british_count(state: GameState) -> int:
    return sum(
        1 for unit in state.british_units.values() if unit.morale is BritishMorale.LOW
    )


def removed_british_count(state: GameState) -> int:
    return sum(
        1 for unit in state.british_units.values() if unit.morale is BritishMorale.REMOVED
    )


def current_activation_summary(state: GameState) -> str:
    activation = state.current_activation
    if activation is None:
        return "-"
    if activation.planned_orders:
        orders = ",".join(order.value for order in activation.planned_orders)
    else:
        orders = "-"
    return (
        f"{activation.active_unit_id} roll={activation.roll} die={activation.selected_die} "
        f"orders={orders} next={activation.next_order_index}"
    )


def state_summary(state: GameState) -> str:
    british_bits = []
    for unit_id in sorted(state.british_units):
        unit = state.british_units[unit_id]
        british_bits.append(
            f"{unit_id}@({unit.position.q},{unit.position.r})/{unit.morale.value}/c{unit.cover}",
        )

    german_bits = []
    for unit_id in sorted(state.german_units):
        unit = state.german_units[unit_id]
        german_bits.append(
            (
                f"{unit_id}@({unit.position.q},{unit.position.r})/"
                f"{unit.unit_class}/{unit.status.value}/{unit.facing.value}"
            ),
        )

    unresolved = sorted(
        f"{marker_id}@({marker.position.q},{marker.position.r})"
        for marker_id, marker in state.unresolved_markers.items()
    )

    return (
        f"turn={state.turn} phase={state.phase.value} kind={state.pending_decision.kind.value} "
        f"active_germans={active_german_count(state)} unresolved={len(state.unresolved_markers)} "
        f"low_british={low_british_count(state)} removed_british={removed_british_count(state)} "
        f"activation=[{current_activation_summary(state)}] "
        f"british=[{' ; '.join(british_bits)}] "
        f"germans=[{' ; '.join(german_bits) if german_bits else '-'}] "
        f"markers=[{' ; '.join(unresolved) if unresolved else '-'}]"
    )


def row_signature(state: GameState) -> str | None:
    activation = state.current_activation
    if activation is None or activation.selected_die is None:
        return None
    active_unit = state.british_units[activation.active_unit_id]
    row = lookup_orders_chart_row(
        state.mission,
        unit_class=active_unit.unit_class,
        die_value=activation.selected_die,
    )
    second = "-" if row.second_order is None else row.second_order.value
    return f"{row.first_order.value}+{second}"


def default_policy_audit_dir(mission_path: Path, agent_name: str) -> Path:
    """Return the default local policy-audit artifact directory."""

    mission = load_mission(mission_path)
    safe_agent = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in agent_name)
    return (
        Path(".project_local/artifacts")
        / f"{mission.mission_id}_{safe_agent}_policy_audit_artifact"
    )


@dataclass(frozen=True, slots=True)
class PolicyAuditStateRow:
    reach_prob: float
    value_pi: float
    value_star: float
    chosen_q_star: float
    local_exact_regret: float
    weighted_exact_regret: float
    loss_mass: float
    turn: int
    phase: str
    decision_kind: str
    is_multi_action: int
    legal_action_count: int
    chosen_action_label: str | None
    active_unit_id: str | None
    row_signature: str | None
    active_germans: int
    unresolved_markers: int
    low_british: int
    removed_british: int
    root_distance: int


@dataclass(frozen=True, slots=True)
class PolicyAuditVerificationResult:
    artifact_dir: Path
    mission_id: str
    mission_path: Path
    policy_root_value_metadata: float
    policy_root_value_lookup: float | None
    policy_root_value_match: bool
    exact_artifact_dir: Path
    state_row_count: int
    decision_summary_count: int
    action_value_row_count: int
    stores_action_values: bool
    exact_action_values_reused: bool | None
    artifact_format: str
    key_codec_version: str

    def to_payload(self) -> dict[str, object]:
        return {
            "artifact_dir": str(self.artifact_dir),
            "mission_id": self.mission_id,
            "mission_path": str(self.mission_path),
            "policy_root_value_metadata": self.policy_root_value_metadata,
            "policy_root_value_lookup": self.policy_root_value_lookup,
            "policy_root_value_match": self.policy_root_value_match,
            "exact_artifact_dir": str(self.exact_artifact_dir),
            "state_row_count": self.state_row_count,
            "decision_summary_count": self.decision_summary_count,
            "action_value_row_count": self.action_value_row_count,
            "stores_action_values": self.stores_action_values,
            "exact_action_values_reused": self.exact_action_values_reused,
            "artifact_format": self.artifact_format,
            "key_codec_version": self.key_codec_version,
        }


class PolicyAuditArtifact:
    """Readonly lookup over a policy-audit artifact."""

    def __init__(
        self,
        *,
        artifact_dir: Path,
    ) -> None:
        self.artifact_dir = Path(artifact_dir)
        self.metadata_path = self.artifact_dir / "metadata.json"
        self.db_path = self.artifact_dir / "policy_audit.sqlite3"
        self.metadata = json.loads(self.metadata_path.read_text())
        self.connection = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)

    def lookup_state_row_key(self, key: bytes) -> PolicyAuditStateRow | None:
        row = self.connection.execute(
            "SELECT "
            "reach_prob, value_pi, value_star, chosen_q_star, local_exact_regret, "
            "weighted_exact_regret, loss_mass, turn, phase, decision_kind, "
            "is_multi_action, legal_action_count, chosen_action_label, active_unit_id, "
            "row_signature, active_germans, unresolved_markers, low_british, "
            "removed_british, root_distance "
            "FROM states WHERE key = ?",
            (sqlite3.Binary(key),),
        ).fetchone()
        if row is None:
            return None
        return PolicyAuditStateRow(*row)

    def close(self) -> None:
        self.connection.close()


class PolicyAuditSink:
    """Incremental SQLite writer for policy-audit artifacts."""

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
            "CREATE TABLE states ("
            " key BLOB PRIMARY KEY,"
            " reach_prob REAL NOT NULL,"
            " value_pi REAL NOT NULL,"
            " value_star REAL NOT NULL,"
            " chosen_q_star REAL NOT NULL,"
            " local_exact_regret REAL NOT NULL,"
            " weighted_exact_regret REAL NOT NULL,"
            " loss_mass REAL NOT NULL,"
            " turn INTEGER NOT NULL,"
            " phase TEXT NOT NULL,"
            " decision_kind TEXT NOT NULL,"
            " is_multi_action INTEGER NOT NULL,"
            " legal_action_count INTEGER NOT NULL,"
            " chosen_action_label TEXT,"
            " active_unit_id TEXT,"
            " row_signature TEXT,"
            " active_germans INTEGER NOT NULL,"
            " unresolved_markers INTEGER NOT NULL,"
            " low_british INTEGER NOT NULL,"
            " removed_british INTEGER NOT NULL,"
            " root_distance INTEGER NOT NULL"
            ") WITHOUT ROWID",
        )
        self.connection.execute(
            "CREATE TABLE decision_summaries ("
            " key BLOB PRIMARY KEY,"
            " state_summary TEXT NOT NULL"
            ") WITHOUT ROWID",
        )
        if self.store_action_values:
            self.connection.execute(
                "CREATE TABLE action_values ("
                " key BLOB NOT NULL,"
                " action_label TEXT NOT NULL,"
                " action_repr TEXT NOT NULL,"
                " q_star REAL NOT NULL,"
                " q_pi REAL NOT NULL,"
                " exact_regret REAL NOT NULL,"
                " policy_advantage REAL NOT NULL,"
                " is_exact_optimal INTEGER NOT NULL,"
                " is_policy_optimal INTEGER NOT NULL,"
                " PRIMARY KEY (key, action_label, action_repr)"
                ") WITHOUT ROWID",
            )
        self.pending_states: list[tuple] = []
        self.pending_summaries: list[tuple] = []
        self.pending_actions: list[tuple] = []
        self.inserted_states = 0
        self.inserted_summaries = 0
        self.inserted_actions = 0
        self.updated_reach = 0
        self.started = time.monotonic()
        self.last_report = self.started

    def add_state(self, row: tuple) -> None:
        self.pending_states.append(row)
        if len(self.pending_states) >= self.insert_batch_size:
            self.flush_inserts()

    def add_summary(self, row: tuple) -> None:
        self.pending_summaries.append(row)
        if len(self.pending_summaries) >= self.insert_batch_size:
            self.flush_inserts()

    def add_action_rows(self, rows: list[tuple]) -> None:
        if not self.store_action_values or not rows:
            return
        self.pending_actions.extend(rows)
        if len(self.pending_actions) >= self.insert_batch_size:
            self.flush_inserts()

    def flush_inserts(self, *, force: bool = False) -> None:
        if not self.pending_states and not self.pending_summaries and not self.pending_actions:
            return
        with self.connection:
            if self.pending_states:
                self.connection.executemany(
                    "INSERT OR IGNORE INTO states("
                    "key, reach_prob, value_pi, value_star, chosen_q_star, local_exact_regret, "
                    "weighted_exact_regret, loss_mass, turn, phase, decision_kind, "
                    "is_multi_action, "
                    "legal_action_count, chosen_action_label, active_unit_id, row_signature, "
                    "active_germans, unresolved_markers, low_british, removed_british, "
                    "root_distance"
                    ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    self.pending_states,
                )
                self.inserted_states += len(self.pending_states)
                self.pending_states.clear()
            if self.pending_summaries:
                self.connection.executemany(
                    "INSERT OR IGNORE INTO decision_summaries(key, state_summary) VALUES (?, ?)",
                    self.pending_summaries,
                )
                self.inserted_summaries += len(self.pending_summaries)
                self.pending_summaries.clear()
            if self.pending_actions:
                self.connection.executemany(
                    "INSERT OR IGNORE INTO action_values("
                    "key, action_label, action_repr, q_star, q_pi, exact_regret, policy_advantage, "
                    "is_exact_optimal, is_policy_optimal"
                    ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    self.pending_actions,
                )
                self.inserted_actions += len(self.pending_actions)
                self.pending_actions.clear()
        self._report(prefix="[export-insert]", force=force)

    def apply_reach_updates(self, items: list[tuple[float, bytes]], *, force: bool = False) -> None:
        if not items:
            return
        with self.connection:
            self.connection.executemany(
                "UPDATE states SET reach_prob = ? WHERE key = ?",
                items,
            )
        self.updated_reach += len(items)
        self._report(prefix="[export-reach]", force=force)

    def finalize_metrics(self) -> None:
        with self.connection:
            self.connection.execute(
                "UPDATE states "
                "SET weighted_exact_regret = reach_prob * local_exact_regret, "
                "    loss_mass = reach_prob * (1.0 - value_pi)",
            )
            self.connection.execute(
                "CREATE INDEX idx_states_weighted_regret ON states(weighted_exact_regret DESC)",
            )
            self.connection.execute(
                "CREATE INDEX idx_states_loss_mass ON states(loss_mass DESC)",
            )
            self.connection.execute(
                "CREATE INDEX idx_states_decision_kind ON states(decision_kind)",
            )
            self.connection.execute(
                "CREATE INDEX idx_states_turn_kind ON states(turn, decision_kind)",
            )
            if self.store_action_values:
                self.connection.execute(
                    "CREATE INDEX idx_action_values_qpi ON action_values(q_pi DESC)",
                )
                self.connection.execute(
                    "CREATE INDEX idx_action_values_qstar ON action_values(q_star DESC)",
                )
        self._report(prefix="[export-finalize]", force=True)

    def count_rows(self) -> tuple[int, int, int]:
        row_count = int(self.connection.execute("SELECT COUNT(*) FROM states").fetchone()[0])
        summary_count = int(
            self.connection.execute("SELECT COUNT(*) FROM decision_summaries").fetchone()[0],
        )
        action_count = (
            int(self.connection.execute("SELECT COUNT(*) FROM action_values").fetchone()[0])
            if self.store_action_values
            else 0
        )
        return row_count, summary_count, action_count

    def close(self) -> None:
        self.flush_inserts(force=True)
        self.connection.close()

    def _report(self, *, prefix: str, force: bool = False) -> None:
        now = time.monotonic()
        if not force and now - self.last_report < self.progress_interval_sec:
            return
        print(
            f"{prefix} "
            f"states={self.inserted_states} "
            f"summaries={self.inserted_summaries} "
            f"actions={self.inserted_actions} "
            f"reach_updates={self.updated_reach} "
            f"elapsed={now - self.started:.1f}s",
            flush=True,
        )
        self.last_report = now


def build_policy_audit_artifact(
    *,
    mission_path: Path,
    exact_artifact_dir: Path | None,
    build_agent: Callable[[], Agent],
    agent_name: str,
    artifact_dir: Path | None = None,
    progress_interval_sec: float = 30.0,
    insert_batch_size: int = 50_000,
    cap_metric: str = "auto",
    memory_cap_gb: float = 20.0,
    memory_low_water_gb: float = 17.0,
    trim_check_interval: int = 2048,
    min_trim_entries: int = 8192,
    cache_through_turn: int | None = None,
    overwrite: bool = False,
    store_action_values: bool = False,
    exact_tie_tolerance: float = EXACT_TIE_TOLERANCE_DEFAULT,
    policy_tie_tolerance: float = EXACT_TIE_TOLERANCE_DEFAULT,
) -> dict[str, object]:
    """Build a policy-audit artifact and return its metadata payload."""

    mission_path = Path(mission_path)
    mission = load_mission(mission_path)
    artifact_dir = (
        Path(artifact_dir)
        if artifact_dir is not None
        else default_policy_audit_dir(mission_path, agent_name)
    )
    artifact_dir.mkdir(parents=True, exist_ok=True)
    db_path = artifact_dir / "policy_audit.sqlite3"
    metadata_path = artifact_dir / "metadata.json"
    tmp_db_path = artifact_dir / "policy_audit.tmp.sqlite3"
    tmp_metadata_path = artifact_dir / "metadata.tmp.json"

    if not overwrite and (db_path.exists() or metadata_path.exists()):
        raise FileExistsError(
            f"artifact already exists at {artifact_dir}; pass overwrite=True to rebuild",
        )

    for path in (tmp_db_path, tmp_metadata_path):
        if path.exists():
            path.unlink()

    exact_artifact_dir = (
        Path(exact_artifact_dir)
        if exact_artifact_dir is not None
        else default_exact_artifact_dir(mission_path)
    )
    exact_artifact = ExactArtifact(
        db_path=resolve_exact_db_path(exact_artifact_dir),
        metadata_path=exact_artifact_dir / "metadata.json",
        mission_path=mission_path,
    )
    sink = PolicyAuditSink(
        db_path=tmp_db_path,
        insert_batch_size=insert_batch_size,
        progress_interval_sec=progress_interval_sec,
        store_action_values=store_action_values,
    )

    build_started = time.monotonic()
    phase_started = build_started
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
    original_get = solver.cache.get

    def artifact_first_get(turn: int, progress_bucket: int, key: bytes):
        value = exact_artifact.lookup_key(key)
        if value is not None:
            return value
        return original_get(turn, progress_bucket, key)

    solver.cache.get = artifact_first_get  # type: ignore[method-assign]

    agent = build_agent()

    def pick_action(state: GameState, legal_actions: tuple[GameAction, ...]) -> GameAction:
        return agent.select_action(state, legal_actions)

    (
        H,
        policy_q_value_impl,
        choose_action_for_state,
        policy_successors,
        maybe_report_policy_progress,
    ) = solver.build_policy_engine(pick_action)
    exact_action_values_available = exact_artifact.has_action_values()

    root_state = create_initial_game_state(mission, seed=0)
    print("=== Phase 1: Policy Value Solve ===", flush=True)
    root_value_pi = H(root_state)
    maybe_report_policy_progress(force=True)
    phase1_elapsed = time.monotonic() - phase_started
    print(f"[phase1] root_value_pi={root_value_pi:.12f} elapsed={phase1_elapsed:.1f}s", flush=True)

    print("\n=== Phase 2: Reach Traversal / Static Export ===", flush=True)
    phase_started = time.monotonic()
    root_state_norm, root_key = solver.normalize_state(root_state)
    root_distance = {root_key: 0}
    reach_prob: dict[bytes, float] = {root_key: 1.0}
    pending_mass: dict[bytes, float] = {root_key: 1.0}
    queue = deque([root_key])
    queued = {root_key}
    frontier_state: dict[bytes, GameState] = {}
    successor_cache: dict[bytes, tuple[tuple[bytes, float], ...]] = {}
    seen_keys: set[bytes] = set()
    last_report = time.monotonic()

    def register_state(state: GameState, key: bytes, *, distance: int) -> None:
        if key in seen_keys:
            return
        seen_keys.add(key)
        frontier_state[key] = state

        legal_actions = (
            ()
            if state.terminal_outcome is not None
            else tuple(resolver_legal_actions(state))
        )
        legal_action_count = len(legal_actions)
        is_multi_action = int(legal_action_count > 1)
        chosen_action = (
            None
            if state.terminal_outcome is not None
            else choose_action_for_state(state, key)
        )
        chosen_action_label = None if chosen_action is None else action_label(chosen_action)
        value_pi = H(state)
        if state.terminal_outcome is TerminalOutcome.VICTORY:
            value_star = 1.0
        elif state.terminal_outcome is TerminalOutcome.DEFEAT:
            value_star = 0.0
        else:
            value_star_lookup = exact_artifact.lookup_key(key)
            value_star = value_star_lookup if value_star_lookup is not None else solver.value(state)

        q_star_by_action: dict[tuple[str, str], float] = {}
        if legal_action_count > 1:
            if exact_action_values_available:
                rows = exact_artifact.lookup_action_values_key(key)
                if rows:
                    q_star_by_action = {
                        (row.action_label, row.action_repr): row.q_star for row in rows
                    }
            missing_q_star = False
            for action in legal_actions:
                label_text = action_label(action)
                repr_text = repr(action)
                if (label_text, repr_text) not in q_star_by_action:
                    missing_q_star = True
                    break
            if missing_q_star:
                q_star_by_action = {
                    (action_label(action), repr(action)): solver.q_value(state, action)
                    for action in legal_actions
                }

        if chosen_action is None or legal_action_count <= 1:
            chosen_q_star = value_star
            local_exact_regret = 0.0
        else:
            chosen_q_star = q_star_by_action[(action_label(chosen_action), repr(chosen_action))]
            local_exact_regret = max(0.0, value_star - chosen_q_star)

        activation = state.current_activation
        sink.add_state(
            (
                sqlite3.Binary(key),
                0.0,
                value_pi,
                value_star,
                chosen_q_star,
                local_exact_regret,
                0.0,
                0.0,
                state.turn,
                state.phase.value,
                state.pending_decision.kind.value,
                is_multi_action,
                legal_action_count,
                chosen_action_label,
                None if activation is None else activation.active_unit_id,
                row_signature(state),
                active_german_count(state),
                len(state.unresolved_markers),
                low_british_count(state),
                removed_british_count(state),
                distance,
            ),
        )
        if is_multi_action:
            sink.add_summary((sqlite3.Binary(key), state_summary(state)))
            if store_action_values:
                q_pi_rows = [
                    (
                        action,
                        q_star_by_action[(action_label(action), repr(action))],
                        policy_q_value_impl(state, action),
                    )
                    for action in legal_actions
                ]
                best_q_star = max(q_star for _action, q_star, _q_pi in q_pi_rows)
                best_q_pi = max(q_pi for _action, _q_star, q_pi in q_pi_rows)
                sink.add_action_rows(
                    [
                        (
                            sqlite3.Binary(key),
                            action_label(action),
                            repr(action),
                            q_star,
                            q_pi,
                            max(0.0, value_star - q_star),
                            max(0.0, best_q_pi - q_pi),
                            1 if best_q_star - q_star <= exact_tie_tolerance else 0,
                            1 if best_q_pi - q_pi <= policy_tie_tolerance else 0,
                        )
                        for action, q_star, q_pi in q_pi_rows
                    ],
                )

    register_state(root_state_norm, root_key, distance=0)

    while queue:
        key = queue.popleft()
        queued.remove(key)
        delta = pending_mass.pop(key, 0.0)
        if delta <= 0.0:
            continue
        if key in successor_cache:
            successors = successor_cache[key]
        else:
            state = frontier_state.pop(key)
            _state, _key, _chosen_action, raw_successors = policy_successors(state)
            aggregated = Counter()
            current_distance = root_distance[key]
            for next_raw_state, probability in raw_successors:
                next_state, next_key = solver.normalize_state(next_raw_state)
                aggregated[next_key] += probability
                if next_key not in reach_prob:
                    root_distance[next_key] = current_distance + 1
                    reach_prob[next_key] = 0.0
                    register_state(next_state, next_key, distance=current_distance + 1)
            successors = tuple(aggregated.items())
            successor_cache[key] = successors

        for next_key, probability in successors:
            mass = delta * probability
            if mass <= 0.0:
                continue
            reach_prob[next_key] += mass
            pending_mass[next_key] = pending_mass.get(next_key, 0.0) + mass
            if next_key not in queued:
                queue.append(next_key)
                queued.add(next_key)

        now = time.monotonic()
        if now - last_report >= progress_interval_sec:
            sink.flush_inserts()
            print(
                "[policy-traverse] "
                f"seen={len(seen_keys)} "
                f"expanded={len(successor_cache)} "
                f"frontier={len(queue)} "
                f"reach_states={len(reach_prob)} "
                f"elapsed={now - phase_started:.1f}s",
                flush=True,
            )
            last_report = now

    sink.flush_inserts(force=True)
    phase2_elapsed = time.monotonic() - phase_started
    print(
        "[phase2] "
        f"seen={len(seen_keys)} "
        f"expanded={len(successor_cache)} "
        f"elapsed={phase2_elapsed:.1f}s",
        flush=True,
    )

    print("\n=== Phase 3: Reach Updates / Finalization ===", flush=True)
    phase_started = time.monotonic()
    update_batch: list[tuple[float, bytes]] = []
    updated = 0
    for key, probability in reach_prob.items():
        update_batch.append((probability, sqlite3.Binary(key)))
        if len(update_batch) >= insert_batch_size:
            sink.apply_reach_updates(update_batch)
            updated += len(update_batch)
            print(
                "[phase3] "
                f"reach_rows={updated}/{len(reach_prob)} "
                f"elapsed={time.monotonic() - phase_started:.1f}s",
                flush=True,
            )
            update_batch.clear()
    if update_batch:
        sink.apply_reach_updates(update_batch, force=True)
        updated += len(update_batch)
        print(
            "[phase3] "
            f"reach_rows={updated}/{len(reach_prob)} "
            f"elapsed={time.monotonic() - phase_started:.1f}s",
            flush=True,
        )

    sink.finalize_metrics()
    row_count, summary_count, action_row_count = sink.count_rows()
    sink.close()
    phase3_elapsed = time.monotonic() - phase_started

    db_size_bytes = tmp_db_path.stat().st_size
    metadata = {
        "artifact_format": POLICY_AUDIT_ARTIFACT_FORMAT,
        "mission_id": mission.mission_id,
        "mission_path": str(mission_path),
        "agent_name": agent_name,
        "uses_exact_artifact_for_value_star": True,
        "exact_artifact_dir": str(exact_artifact_dir),
        "exact_root_value": float(exact_artifact.metadata["root_value"]),
        "policy_root_value": root_value_pi,
        "state_row_count": row_count,
        "decision_summary_count": summary_count,
        "stores_action_values": bool(store_action_values),
        "action_value_row_count": int(action_row_count),
        "exact_action_values_reused": bool(exact_action_values_available),
        "exact_tie_tolerance": float(exact_tie_tolerance),
        "policy_tie_tolerance": float(policy_tie_tolerance),
        "policy_tie_break_rule": (
            "maximize q_pi; among ties within tolerance choose current policy action label "
            "stored on states"
        ),
        "db_size_bytes": int(db_size_bytes),
        "db_size_mb": round(db_size_bytes / (1024 * 1024), 3),
        "phase1_policy_value_elapsed_sec": round(phase1_elapsed, 3),
        "phase2_traversal_elapsed_sec": round(phase2_elapsed, 3),
        "phase3_finalize_elapsed_sec": round(phase3_elapsed, 3),
        "build_elapsed_sec": round(time.monotonic() - build_started, 3),
        "insert_batch_size": insert_batch_size,
        "cap_metric": cap_metric,
        "memory_cap_gb": memory_cap_gb,
        "memory_low_water_gb": memory_low_water_gb,
        "trim_check_interval": trim_check_interval,
        "min_trim_entries": min_trim_entries,
        "cache_through_turn": cache_through_turn,
        "stores_observed": int(solver.cache.stores),
        "evictions_observed": int(solver.cache.evictions),
        "trims_observed": int(solver.cache.trims),
        "uses_british_swap_symmetry": bool(
            exact_artifact.metadata.get("uses_british_swap_symmetry", False),
        ),
        "key_codec_version": exact_artifact.metadata["key_codec_version"],
    }
    tmp_metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n")
    if db_path.exists():
        db_path.unlink()
    if metadata_path.exists():
        metadata_path.unlink()
    tmp_db_path.replace(db_path)
    tmp_metadata_path.replace(metadata_path)
    exact_artifact.close()
    return metadata


def read_policy_audit_stats(artifact_dir: Path) -> dict[str, object]:
    """Read policy-audit metadata."""

    return json.loads((Path(artifact_dir) / "metadata.json").read_text())


def verify_policy_audit_artifact(artifact_dir: Path) -> PolicyAuditVerificationResult:
    """Verify that the policy root value stored in metadata matches the root row."""

    artifact_dir = Path(artifact_dir)
    metadata = read_policy_audit_stats(artifact_dir)
    mission_path = Path(str(metadata["mission_path"]))
    root_state = create_initial_game_state(load_mission(mission_path), seed=0)
    exact_artifact = ExactArtifact(
        db_path=resolve_exact_db_path(Path(str(metadata["exact_artifact_dir"]))),
        metadata_path=Path(str(metadata["exact_artifact_dir"])) / "metadata.json",
        mission_path=mission_path,
    )
    policy_artifact = PolicyAuditArtifact(artifact_dir=artifact_dir)
    try:
        root_key = exact_artifact.codec.pack_canonical(root_state)
        root_row = policy_artifact.lookup_state_row_key(root_key)
    finally:
        exact_artifact.close()
        policy_artifact.close()

    lookup_value = None if root_row is None else root_row.value_pi
    return PolicyAuditVerificationResult(
        artifact_dir=artifact_dir,
        mission_id=str(metadata["mission_id"]),
        mission_path=mission_path,
        policy_root_value_metadata=float(metadata["policy_root_value"]),
        policy_root_value_lookup=lookup_value,
        policy_root_value_match=lookup_value == metadata["policy_root_value"],
        exact_artifact_dir=Path(str(metadata["exact_artifact_dir"])),
        state_row_count=int(metadata["state_row_count"]),
        decision_summary_count=int(metadata["decision_summary_count"]),
        action_value_row_count=int(metadata.get("action_value_row_count", 0)),
        stores_action_values=bool(metadata.get("stores_action_values", False)),
        exact_action_values_reused=metadata.get("exact_action_values_reused"),
        artifact_format=str(metadata["artifact_format"]),
        key_codec_version=str(metadata["key_codec_version"]),
    )


__all__ = [
    "POLICY_AUDIT_ARTIFACT_FORMAT",
    "PolicyAuditArtifact",
    "PolicyAuditSink",
    "PolicyAuditStateRow",
    "PolicyAuditVerificationResult",
    "active_german_count",
    "build_policy_audit_artifact",
    "current_activation_summary",
    "default_policy_audit_dir",
    "low_british_count",
    "read_policy_audit_stats",
    "removed_british_count",
    "row_signature",
    "state_summary",
    "verify_policy_audit_artifact",
]
