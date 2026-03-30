"""Generic exact/policy solver core for exact-solved missions.

This module productizes the stable local Mission 1/2 exact-guided workflow
without importing `.project_local` code at runtime. It provides:

- a packed canonical public-state codec suitable for artifact keys;
- a bounded exact solver for fair exact mission values;
- exact fixed-policy evaluation helpers used by policy-audit artifacts.

The heavy exact solve remains operator-owned. This module is a reusable tracked
library surface, not a promise that every exact-solved mission should be solved
interactively by default.
"""

from __future__ import annotations

import os
import resource
import subprocess
import sys
import time
from collections import Counter, OrderedDict
from collections.abc import Callable
from dataclasses import dataclass, replace
from itertools import product
from pathlib import Path
from typing import Protocol

import solo_wargame_ai.domain.legal_actions as legal_actions_module
from solo_wargame_ai.domain.actions import (
    AdvanceAction,
    ChooseOrderExecutionAction,
    DiscardActivationRollAction,
    FireAction,
    GameAction,
    GrenadeAttackAction,
    RallyAction,
    ResolveDoubleChoiceAction,
    ScoutAction,
    SelectActivationDieAction,
    SelectBritishUnitAction,
    SelectGermanUnitAction,
    TakeCoverAction,
)
from solo_wargame_ai.domain.combat import (
    calculate_fire_threshold,
    calculate_grenade_attack_threshold,
    degrade_british_morale,
)
from solo_wargame_ai.domain.decision_context import (
    ChooseActivationDieContext,
    ChooseBritishUnitContext,
    ChooseDoubleChoiceContext,
    ChooseGermanUnitContext,
    ChooseOrderExecutionContext,
    ChooseOrderParameterContext,
    DecisionContextKind,
)
from solo_wargame_ai.domain.enums import HexDirection
from solo_wargame_ai.domain.german_fire import (
    calculate_german_fire_threshold,
    german_fire_target_ids,
    selectable_german_unit_ids,
)
from solo_wargame_ai.domain.legal_actions import get_legal_actions, lookup_orders_chart_row
from solo_wargame_ai.domain.mission import MissionObjectiveKind, OrderName
from solo_wargame_ai.domain.reveal import facing_toward_adjacent_hex, movement_reveal_marker_ids
from solo_wargame_ai.domain.state import (
    CurrentActivation,
    GamePhase,
    GameState,
    TerminalOutcome,
    create_initial_game_state,
)
from solo_wargame_ai.domain.units import BritishMorale, GermanUnitStatus, RevealedGermanUnitState
from solo_wargame_ai.io import load_mission

if sys.platform == "darwin":
    import ctypes

    _libsystem = ctypes.CDLL("/usr/lib/libSystem.B.dylib", use_errno=True)
    _mach_task_self = _libsystem.mach_task_self
    _mach_task_self.restype = ctypes.c_uint
    _task_info = _libsystem.task_info
    _task_info.argtypes = [
        ctypes.c_uint,
        ctypes.c_int,
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_uint),
    ]
    _task_info.restype = ctypes.c_int
    _TASK_VM_INFO = 22

    class _TaskVmInfoRev1(ctypes.Structure):
        _fields_ = [
            ("virtual_size", ctypes.c_uint64),
            ("region_count", ctypes.c_int),
            ("page_size", ctypes.c_int),
            ("resident_size", ctypes.c_uint64),
            ("resident_size_peak", ctypes.c_uint64),
            ("device", ctypes.c_uint64),
            ("device_peak", ctypes.c_uint64),
            ("internal", ctypes.c_uint64),
            ("internal_peak", ctypes.c_uint64),
            ("external", ctypes.c_uint64),
            ("external_peak", ctypes.c_uint64),
            ("reusable", ctypes.c_uint64),
            ("reusable_peak", ctypes.c_uint64),
            ("purgeable_volatile_pmap", ctypes.c_uint64),
            ("purgeable_volatile_resident", ctypes.c_uint64),
            ("purgeable_volatile_virtual", ctypes.c_uint64),
            ("compressed", ctypes.c_uint64),
            ("compressed_peak", ctypes.c_uint64),
            ("compressed_lifetime", ctypes.c_uint64),
            ("phys_footprint", ctypes.c_uint64),
        ]

    _TASK_VM_INFO_REV1_COUNT = ctypes.sizeof(_TaskVmInfoRev1) // ctypes.sizeof(ctypes.c_uint)


EXACT_KEY_CODEC_VERSION = "mission_packed_public_state_v1"
EXACT_TIE_TOLERANCE_DEFAULT = 1e-15


def current_rss_bytes() -> int:
    """Return current resident set size in bytes when available."""

    try:
        output = subprocess.check_output(
            ["ps", "-o", "rss=", "-p", str(os.getpid())],
            text=True,
        )
        return int(output.strip()) * 1024
    except Exception:
        rss_units = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        if sys.platform == "darwin":
            return int(rss_units)
        return int(rss_units) * 1024


def current_footprint_bytes() -> int | None:
    """Return macOS phys_footprint when available."""

    if sys.platform != "darwin":
        return None

    try:
        info = _TaskVmInfoRev1()
        count = ctypes.c_uint(_TASK_VM_INFO_REV1_COUNT)
        result = _task_info(
            _mach_task_self(),
            _TASK_VM_INFO,
            ctypes.byref(info),
            ctypes.byref(count),
        )
        if result != 0 or count.value < _TASK_VM_INFO_REV1_COUNT:
            return None
        return int(info.phys_footprint)
    except Exception:
        return None


def resolve_cap_metric(cap_metric: str) -> tuple[str, Callable[[], int]]:
    """Choose the memory metric used to trigger trimming."""

    if cap_metric == "rss":
        return "rss", current_rss_bytes

    footprint_bytes = current_footprint_bytes()
    if cap_metric == "footprint":
        if footprint_bytes is None:
            raise RuntimeError("macOS phys_footprint is unavailable for this process")
        return "footprint", lambda: current_footprint_bytes() or current_rss_bytes()

    if footprint_bytes is not None:
        return "footprint", lambda: current_footprint_bytes() or current_rss_bytes()
    return "rss", current_rss_bytes


def action_label(action: GameAction) -> str:
    """Return a compact stable action label for artifact storage."""

    if isinstance(action, SelectBritishUnitAction):
        return f"select_unit:{action.unit_id}"
    if isinstance(action, SelectActivationDieAction):
        return f"select_die:{action.die_value}"
    if isinstance(action, ResolveDoubleChoiceAction):
        return f"double:{action.choice.value}"
    if isinstance(action, ChooseOrderExecutionAction):
        return f"exec:{action.choice.value}"
    if isinstance(action, AdvanceAction):
        return f"advance:{action.destination.q},{action.destination.r}"
    if isinstance(action, ScoutAction):
        facing = "-" if action.facing is None else action.facing.value
        return f"scout:{action.marker_id}:{facing}"
    return repr(action)


class PickAction(Protocol):
    def __call__(
        self,
        state: GameState,
        legal_actions: tuple[GameAction, ...],
    ) -> GameAction: ...


class PackedPublicStateCodec:
    """Packed canonical public-state codec used by exact/policy artifacts."""

    def __init__(self, mission_path: Path) -> None:
        self.mission_path = Path(mission_path)
        mission = load_mission(self.mission_path)
        self.mission = mission
        british_symmetry_ids = tuple(unit.unit_id for unit in mission.british.roster)
        self.british_symmetry_ids = british_symmetry_ids
        self.use_british_swap_symmetry = (
            len(mission.british.roster) == 2
            and len({unit.unit_class for unit in mission.british.roster}) == 1
        )
        self.british_slot_by_id = {
            unit_id: index for index, unit_id in enumerate(british_symmetry_ids)
        }
        marker_ids = tuple(marker.marker_id for marker in mission.map.hidden_markers)
        self.marker_ids = marker_ids
        self.marker_slot_by_id = {marker_id: index for index, marker_id in enumerate(marker_ids)}
        self.coord_index = {
            map_hex.coord: index + 1 for index, map_hex in enumerate(mission.map.hexes)
        }
        self.turn_width = 1 if mission.turns.turn_limit <= 0xFF else 2
        self.british_mask_width = max(1, (len(british_symmetry_ids) + 7) // 8)
        self.german_mask_width = max(1, (len(marker_ids) + 7) // 8)
        self.position_width = 1 if len(self.coord_index) <= 0xFF else 2
        self.order_code = {order_name: index + 1 for index, order_name in enumerate(OrderName)}
        self.phase_code = {
            GamePhase.BRITISH: 1,
            GamePhase.GERMAN: 2,
        }
        self.decision_code = {
            DecisionContextKind.CHOOSE_BRITISH_UNIT: 1,
            DecisionContextKind.CHOOSE_DOUBLE_CHOICE: 2,
            DecisionContextKind.CHOOSE_ACTIVATION_DIE: 3,
            DecisionContextKind.CHOOSE_ORDER_EXECUTION: 4,
            DecisionContextKind.CHOOSE_ORDER_PARAMETER: 5,
            DecisionContextKind.CHOOSE_GERMAN_UNIT: 6,
        }
        self.terminal_code = {
            None: 0,
            TerminalOutcome.VICTORY: 1,
            TerminalOutcome.DEFEAT: 2,
        }
        self.morale_code = {
            BritishMorale.NORMAL: 1,
            BritishMorale.LOW: 2,
            BritishMorale.REMOVED: 3,
        }
        self.german_status_code = {
            GermanUnitStatus.ACTIVE: 1,
            GermanUnitStatus.REMOVED: 2,
        }
        self.facing_code = {direction: index + 1 for index, direction in enumerate(HexDirection)}
        reveal_unit_classes = sorted(
            {row.result_unit_class for row in mission.german.reveal_table},
        )
        self.german_class_code = {
            unit_class: index + 1 for index, unit_class in enumerate(reveal_unit_classes)
        }
        sample_key = self.pack_canonical(create_initial_game_state(self.mission, seed=0))
        self.sample_key_length_bytes = len(sample_key)

    @staticmethod
    def _append_uint(parts: bytearray, value: int, width: int = 1) -> None:
        parts.extend(int(value).to_bytes(width, "big", signed=False))

    @staticmethod
    def _canon_roll(roll: tuple[int, int] | None) -> tuple[int, int] | None:
        if roll is None:
            return None
        return tuple(sorted(roll))

    def _roll_code(self, roll: tuple[int, int] | None) -> int:
        if roll is None:
            return 0
        low, high = self._canon_roll(roll)
        return low * 8 + high

    def _activated_mask(self, unit_ids: frozenset[str], slot_by_id: dict[str, int]) -> int:
        mask = 0
        for unit_id in unit_ids:
            mask |= 1 << slot_by_id[unit_id]
        return mask

    def pack_raw(self, state: GameState) -> bytes:
        activation = state.current_activation
        parts = bytearray()
        self._append_uint(parts, state.turn, width=self.turn_width)
        self._append_uint(parts, self.phase_code[state.phase])
        self._append_uint(parts, self.decision_code[state.pending_decision.kind])
        self._append_uint(parts, self.terminal_code[state.terminal_outcome])
        self._append_uint(
            parts,
            self._activated_mask(state.activated_british_unit_ids, self.british_slot_by_id),
            width=self.british_mask_width,
        )
        self._append_uint(
            parts,
            self._activated_mask(state.activated_german_unit_ids, self.marker_slot_by_id),
            width=self.german_mask_width,
        )
        self._append_uint(parts, 0 if activation is None else 1)
        if activation is not None:
            self._append_uint(parts, self.british_slot_by_id[activation.active_unit_id] + 1)
            self._append_uint(parts, self._roll_code(activation.roll))
            self._append_uint(
                parts, 0 if activation.selected_die is None else activation.selected_die
            )
            self._append_uint(parts, len(activation.planned_orders))
            self._append_uint(
                parts,
                self.order_code[activation.planned_orders[0]] if activation.planned_orders else 0,
            )
            self._append_uint(
                parts,
                self.order_code[activation.planned_orders[1]]
                if len(activation.planned_orders) > 1
                else 0,
            )
            self._append_uint(parts, activation.next_order_index)

        for unit_id in self.british_symmetry_ids:
            unit = state.british_units[unit_id]
            self._append_uint(parts, self.coord_index[unit.position], width=self.position_width)
            self._append_uint(parts, self.morale_code[unit.morale])
            self._append_uint(parts, unit.cover, width=2)

        for marker_id in self.marker_ids:
            if marker_id in state.unresolved_markers:
                self._append_uint(parts, 0)
                self._append_uint(parts, 0)
                self._append_uint(parts, 0)
                continue
            unit = state.german_units[marker_id]
            self._append_uint(parts, self.german_status_code[unit.status])
            self._append_uint(parts, self.german_class_code[unit.unit_class])
            self._append_uint(parts, self.facing_code[unit.facing])

        return bytes(parts)

    def _swapped_british_state(self, state: GameState) -> GameState | None:
        if not self.use_british_swap_symmetry:
            return None

        first_id, second_id = self.british_symmetry_ids

        def swap_unit_id(unit_id: str) -> str:
            if unit_id == first_id:
                return second_id
            if unit_id == second_id:
                return first_id
            return unit_id

        swapped_units = {
            swap_unit_id(unit_id): replace(unit_state, unit_id=swap_unit_id(unit_id))
            for unit_id, unit_state in state.british_units.items()
        }
        swapped_activation = (
            None
            if state.current_activation is None
            else replace(
                state.current_activation,
                active_unit_id=swap_unit_id(state.current_activation.active_unit_id),
            )
        )
        return replace(
            state,
            british_units=swapped_units,
            activated_british_unit_ids=frozenset(
                swap_unit_id(unit_id) for unit_id in state.activated_british_unit_ids
            ),
            current_activation=swapped_activation,
        )

    def pack_canonical(self, state: GameState) -> bytes:
        best_key = self.pack_raw(state)
        swapped_state = self._swapped_british_state(state)
        if swapped_state is None:
            return best_key
        swapped_key = self.pack_raw(swapped_state)
        if swapped_key < best_key:
            return swapped_key
        return best_key

    def metadata(self) -> dict[str, object]:
        return {
            "mission_id": self.mission.mission_id,
            "mission_path": str(self.mission_path),
            "key_codec_version": EXACT_KEY_CODEC_VERSION,
            "sample_key_length_bytes": self.sample_key_length_bytes,
            "uses_british_swap_symmetry": self.use_british_swap_symmetry,
        }


class TurnAwareValueCache:
    """Turn- and progress-aware bounded exact-value cache."""

    def __init__(
        self,
        *,
        cap_metric: str,
        current_metric_bytes: Callable[[], int],
        cap_bytes: int,
        low_water_bytes: int,
        trim_check_interval: int,
        min_trim_entries: int,
    ) -> None:
        self.cap_metric = cap_metric
        self._current_metric_bytes = current_metric_bytes
        self.cap_bytes = cap_bytes
        self.low_water_bytes = low_water_bytes
        self.trim_check_interval = trim_check_interval
        self.min_trim_entries = min_trim_entries
        self._buckets: dict[tuple[int, int], OrderedDict[bytes, float]] = {}
        self.entries = 0
        self.hits = 0
        self.misses = 0
        self.stores = 0
        self.evictions = 0
        self.trims = 0
        self.base_metric_bytes = current_metric_bytes()
        self.last_metric_bytes = self.base_metric_bytes
        self.last_rss_bytes = current_rss_bytes()
        self.last_footprint_bytes = current_footprint_bytes()
        self.entry_cap: int | None = None

    def get(self, turn: int, progress_bucket: int, key: bytes) -> float | None:
        bucket = self._buckets.get((turn, progress_bucket))
        if bucket is None:
            self.misses += 1
            return None
        try:
            value = bucket.pop(key)
        except KeyError:
            self.misses += 1
            return None
        bucket[key] = value
        self.hits += 1
        return value

    def put(self, turn: int, progress_bucket: int, key: bytes, value: float) -> None:
        bucket = self._buckets.setdefault((turn, progress_bucket), OrderedDict())
        if key in bucket:
            bucket.pop(key)
        else:
            self.entries += 1
            self.stores += 1
        bucket[key] = value
        if self.stores % self.trim_check_interval == 0:
            self.trim_if_needed()

    def trim_if_needed(self) -> int:
        metric = self._current_metric_bytes()
        self.last_metric_bytes = metric
        if metric <= self.cap_bytes or self.entries == 0:
            return metric

        if self.entry_cap is None:
            cache_metric = max(1, metric - self.base_metric_bytes)
            bytes_per_entry = cache_metric / self.entries
            budget = max(0, self.low_water_bytes - self.base_metric_bytes)
            self.entry_cap = max(0, int(budget / bytes_per_entry))

        target_entries = self.entry_cap
        if target_entries >= self.entries:
            target_entries = max(
                0,
                self.entries - max(self.min_trim_entries, self.entries // 20),
            )
        self._evict_batch(self.entries - target_entries)
        self.trims += 1
        self.last_metric_bytes = self._current_metric_bytes()
        return self.last_metric_bytes

    def _evict_batch(self, target: int) -> None:
        remaining = target
        for bucket_key in sorted(self._buckets, reverse=True):
            bucket = self._buckets[bucket_key]
            while bucket and remaining > 0:
                bucket.popitem(last=False)
                self.entries -= 1
                self.evictions += 1
                remaining -= 1
            if not bucket:
                del self._buckets[bucket_key]
            if remaining <= 0:
                return

    def bucket_sizes(self) -> dict[int, int]:
        totals: dict[int, int] = {}
        for (turn, _progress_bucket), bucket in self._buckets.items():
            if not bucket:
                continue
            totals[turn] = totals.get(turn, 0) + len(bucket)
        return {turn: totals[turn] for turn in sorted(totals)}


@dataclass(frozen=True, slots=True)
class ExactPolicySolver:
    """Tracked bounded exact/policy solver surface."""

    mission_path: Path
    codec: PackedPublicStateCodec
    value: Callable[[GameState], float]
    q_value: Callable[[GameState, GameAction], float]
    maybe_report_progress: Callable[..., None]
    cache: TurnAwareValueCache
    normalize_state: Callable[[GameState], tuple[GameState, bytes]]
    build_policy_engine: Callable[[PickAction], tuple[object, ...]]
    evaluate_policy: Callable[..., float]
    policy_q_value: Callable[[PickAction, GameState, GameAction], float]

    @property
    def mission(self):
        return self.codec.mission


def build_capped_exact_policy_solver(
    *,
    mission_path: Path,
    progress_interval_sec: float = 30.0,
    cap_metric: str = "auto",
    memory_cap_gb: float = 20.0,
    memory_low_water_gb: float = 17.0,
    trim_check_interval: int = 2048,
    min_trim_entries: int = 8192,
    cache_through_turn: int | None = None,
    on_state_solved: Callable[
        [GameState, bytes, float, list[tuple[GameAction, float]] | None],
        None,
    ]
    | None = None,
) -> ExactPolicySolver:
    """Build a bounded exact solver and fixed-policy evaluation helpers."""

    codec = PackedPublicStateCodec(Path(mission_path))
    mission = codec.mission
    if mission.objective.kind is not MissionObjectiveKind.CLEAR_ALL_HOSTILES:
        raise ValueError("exact/policy solver currently supports only clear_all_hostiles")

    roll_probs: Counter[tuple[int, int]] = Counter()
    for first_die in range(1, 7):
        for second_die in range(1, 7):
            roll_probs[tuple(sorted((first_die, second_die)))] += 1.0 / 36.0

    two_d6_hit_counts = {
        threshold: sum(
            1
            for first_die in range(1, 7)
            for second_die in range(1, 7)
            if first_die + second_die >= threshold
        )
        for threshold in range(-20, 40)
    }
    reveal_probs: Counter[str] = Counter()
    for row in mission.german.reveal_table:
        reveal_probs[row.result_unit_class] += (row.roll_max - row.roll_min + 1) / 6.0

    effective_cache_through_turn = (
        mission.turns.turn_limit if cache_through_turn is None else cache_through_turn
    )
    selected_cap_metric, current_metric_bytes = resolve_cap_metric(cap_metric)
    cache = TurnAwareValueCache(
        cap_metric=selected_cap_metric,
        current_metric_bytes=current_metric_bytes,
        cap_bytes=int(memory_cap_gb * (1024**3)),
        low_water_bytes=int(memory_low_water_gb * (1024**3)),
        trim_check_interval=trim_check_interval,
        min_trim_entries=min_trim_entries,
    )
    start_time = time.monotonic()
    last_progress = start_time
    solved_by_kind: Counter[str] = Counter()
    q_calls = 0
    value_solves = 0

    def maybe_report_progress(*, force: bool = False) -> None:
        nonlocal last_progress
        now = time.monotonic()
        if not force and now - last_progress < progress_interval_sec:
            return
        rss_mb = current_rss_bytes() / (1024 * 1024)
        footprint_bytes = current_footprint_bytes()
        footprint_text = (
            f"{footprint_bytes / (1024 * 1024):.1f}" if footprint_bytes is not None else "n/a"
        )
        print(
            "[progress] "
            f"elapsed={now - start_time:.1f}s "
            f"rss_mb={rss_mb:.1f} "
            f"footprint_mb={footprint_text} "
            f"cache_entries={cache.entries} "
            f"cache_turns={cache.bucket_sizes()} "
            f"V(hits={cache.hits}, misses={cache.misses}, stores={cache.stores}, "
            f"evictions={cache.evictions}, trims={cache.trims}) "
            f"Q(calls={q_calls}) "
            f"value_solves={value_solves} "
            f"solved={dict(solved_by_kind)}",
            flush=True,
        )
        last_progress = now

    def local_progress_bucket(state: GameState) -> int:
        activation = state.current_activation
        if state.phase is GamePhase.BRITISH:
            completed_units = len(state.activated_british_unit_ids)
            if activation is None:
                stage = 0
            elif state.pending_decision.kind is DecisionContextKind.CHOOSE_DOUBLE_CHOICE:
                stage = 1
            elif state.pending_decision.kind is DecisionContextKind.CHOOSE_ACTIVATION_DIE:
                stage = 2
            elif state.pending_decision.kind is DecisionContextKind.CHOOSE_ORDER_EXECUTION:
                stage = 3
            elif state.pending_decision.kind is DecisionContextKind.CHOOSE_ORDER_PARAMETER:
                stage = (
                    4 + (activation.next_order_index * 2) + min(len(activation.planned_orders), 2)
                )
            else:
                stage = 0
            return completed_units * 16 + stage

        completed_units = len(state.activated_german_unit_ids)
        remaining_active = sum(
            1
            for unit in state.german_units.values()
            if unit.status is GermanUnitStatus.ACTIVE
            and unit.unit_id not in state.activated_german_unit_ids
        )
        return 128 + (completed_units * 16) + max(0, 3 - remaining_active)

    def canonicalize_state(state: GameState) -> tuple[GameState, bytes]:
        best_state = state
        best_key = codec.pack_canonical(state)
        swapped_state = codec._swapped_british_state(state)
        if swapped_state is None:
            return best_state, best_key
        swapped_key = codec.pack_raw(swapped_state)
        if swapped_key < best_key:
            return swapped_state, swapped_key
        return best_state, best_key

    def is_victory(state: GameState) -> bool:
        return not state.unresolved_markers and not any(
            unit.status is GermanUnitStatus.ACTIVE for unit in state.german_units.values()
        )

    def selectable_british_ids(state: GameState) -> tuple[str, ...]:
        return legal_actions_module._selectable_british_unit_ids(
            state,
            activated_british_unit_ids=state.activated_british_unit_ids,
        )

    def auto_progress(state: GameState) -> GameState:
        progressed = state
        while progressed.terminal_outcome is None:
            if is_victory(progressed):
                pending = (
                    ChooseGermanUnitContext()
                    if progressed.phase is GamePhase.GERMAN
                    else ChooseBritishUnitContext()
                )
                progressed = replace(
                    progressed,
                    pending_decision=pending,
                    current_activation=None,
                    terminal_outcome=TerminalOutcome.VICTORY,
                )
                break

            if (
                progressed.phase is GamePhase.GERMAN
                and not selectable_german_unit_ids(progressed)
                and progressed.turn >= progressed.mission.turns.turn_limit
            ):
                progressed = replace(
                    progressed,
                    pending_decision=ChooseGermanUnitContext(),
                    current_activation=None,
                    terminal_outcome=TerminalOutcome.DEFEAT,
                )
                break

            if (
                progressed.phase is GamePhase.BRITISH
                and isinstance(progressed.pending_decision, ChooseBritishUnitContext)
                and progressed.current_activation is None
                and not selectable_british_ids(progressed)
            ):
                progressed = replace(
                    progressed,
                    phase=GamePhase.GERMAN,
                    activated_german_unit_ids=frozenset(),
                    pending_decision=ChooseGermanUnitContext(),
                    current_activation=None,
                )
                continue

            if progressed.phase is GamePhase.GERMAN and not selectable_german_unit_ids(progressed):
                progressed = replace(
                    progressed,
                    turn=progressed.turn + 1,
                    phase=GamePhase.BRITISH,
                    activated_british_unit_ids=frozenset(),
                    activated_german_unit_ids=frozenset(),
                    pending_decision=ChooseBritishUnitContext(),
                    current_activation=None,
                )
                continue
            break
        return progressed

    def normalize_state(state: GameState) -> tuple[GameState, bytes]:
        return canonicalize_state(auto_progress(state))

    def hit_prob(threshold: int) -> float:
        return two_d6_hit_counts.get(threshold, 0) / 36.0

    def should_cache_state(state: GameState) -> bool:
        if state.terminal_outcome is not None:
            return False
        return state.turn <= effective_cache_through_turn

    def finish_activation(state: GameState) -> GameState:
        activation = state.current_activation
        if activation is None:
            raise AssertionError("finish_activation requires current_activation")
        activated_unit_ids = frozenset(
            (*state.activated_british_unit_ids, activation.active_unit_id)
        )
        remaining_units = legal_actions_module._selectable_british_unit_ids(
            state,
            activated_british_unit_ids=activated_unit_ids,
        )
        if remaining_units:
            return replace(
                state,
                activated_british_unit_ids=activated_unit_ids,
                pending_decision=ChooseBritishUnitContext(),
                current_activation=None,
            )
        return replace(
            state,
            phase=GamePhase.GERMAN,
            activated_british_unit_ids=activated_unit_ids,
            activated_german_unit_ids=frozenset(),
            pending_decision=ChooseGermanUnitContext(),
            current_activation=None,
        )

    def deterministic_next(state: GameState, action: GameAction) -> GameState:
        if isinstance(action, SelectActivationDieAction):
            return replace(
                state,
                pending_decision=ChooseOrderExecutionContext(),
                current_activation=replace(state.current_activation, selected_die=action.die_value),
            )
        if isinstance(action, DiscardActivationRollAction):
            return finish_activation(state)
        if isinstance(action, ChooseOrderExecutionAction):
            activation = state.current_activation
            if activation is None:
                raise AssertionError("ChooseOrderExecutionAction requires current_activation")
            active_unit = state.british_units[activation.active_unit_id]
            orders_row = lookup_orders_chart_row(
                state.mission,
                unit_class=active_unit.unit_class,
                die_value=activation.selected_die or 0,
            )
            if action.choice.value == "no_action":
                return finish_activation(state)
            if action.choice.value == "first_order_only":
                planned_orders = (orders_row.first_order,)
            elif action.choice.value == "second_order_only":
                planned_orders = (orders_row.second_order,)
            else:
                planned_orders = (orders_row.first_order, orders_row.second_order)
            return replace(
                state,
                pending_decision=ChooseOrderParameterContext(
                    order=planned_orders[0],
                    order_index=0,
                ),
                current_activation=replace(
                    activation,
                    planned_orders=planned_orders,
                    next_order_index=0,
                ),
            )
        if isinstance(action, TakeCoverAction):
            activation = state.current_activation
            if activation is None:
                raise AssertionError("TakeCoverAction requires current_activation")
            active_unit = state.british_units[activation.active_unit_id]
            british_units = dict(state.british_units)
            british_units[active_unit.unit_id] = replace(active_unit, cover=active_unit.cover + 1)
            return legal_actions_module._continue_after_resolved_order(
                state,
                british_units=british_units,
                german_units=state.german_units,
                unresolved_markers=state.unresolved_markers,
                rng_state=state.rng_state,
            )
        if isinstance(action, RallyAction):
            activation = state.current_activation
            if activation is None:
                raise AssertionError("RallyAction requires current_activation")
            active_unit = state.british_units[activation.active_unit_id]
            british_units = dict(state.british_units)
            british_units[active_unit.unit_id] = replace(
                active_unit,
                morale=(
                    BritishMorale.NORMAL
                    if active_unit.morale is BritishMorale.LOW
                    else active_unit.morale
                ),
            )
            return legal_actions_module._continue_after_resolved_order(
                state,
                british_units=british_units,
                german_units=state.german_units,
                unresolved_markers=state.unresolved_markers,
                rng_state=state.rng_state,
            )
        raise AssertionError(f"Unsupported deterministic action: {type(action)!r}")

    def keep_state_with_double(state: GameState, double_value: int) -> GameState:
        activation = state.current_activation
        if activation is None:
            raise AssertionError("double keep requires current_activation")
        return replace(
            state,
            pending_decision=ChooseActivationDieContext(),
            current_activation=replace(
                activation,
                roll=(double_value, double_value),
                selected_die=None,
                planned_orders=(),
                next_order_index=0,
            ),
        )

    def reroll_value(state: GameState) -> float:
        keep_values = [V(keep_state_with_double(state, die_value)) for die_value in range(1, 7)]
        non_double_total = 0.0
        for roll, prob in roll_probs.items():
            if roll[0] == roll[1]:
                continue
            next_state = replace(
                state,
                pending_decision=ChooseActivationDieContext(),
                current_activation=replace(
                    state.current_activation,
                    roll=roll,
                    selected_die=None,
                    planned_orders=(),
                    next_order_index=0,
                ),
            )
            non_double_total += prob * V(next_state)

        sorted_keep = sorted(keep_values)
        for split_index in range(7):
            candidate = (non_double_total + sum(sorted_keep[split_index:]) / 36.0) / (
                1.0 - split_index / 36.0
            )
            lower_ok = split_index == 0 or sorted_keep[split_index - 1] <= candidate + 1e-15
            upper_ok = split_index == 6 or candidate <= sorted_keep[split_index] + 1e-15
            if lower_ok and upper_ok:
                return candidate
        raise AssertionError("failed to solve reroll fixed point")

    def Q(state: GameState, action: GameAction) -> float:
        nonlocal q_calls
        q_calls += 1

        if isinstance(action, SelectBritishUnitAction):
            total = 0.0
            for roll, prob in roll_probs.items():
                pending = (
                    ChooseDoubleChoiceContext()
                    if roll[0] == roll[1]
                    else ChooseActivationDieContext()
                )
                next_state = replace(
                    state,
                    pending_decision=pending,
                    current_activation=CurrentActivation(active_unit_id=action.unit_id, roll=roll),
                )
                total += prob * V(next_state)
            return total

        if isinstance(action, AdvanceAction):
            activation = state.current_activation
            if activation is None:
                raise AssertionError("Advance requires current_activation")
            active_unit = state.british_units[activation.active_unit_id]
            british_units = dict(state.british_units)
            british_units[active_unit.unit_id] = replace(
                active_unit,
                position=action.destination,
                cover=0,
            )
            marker_ids = movement_reveal_marker_ids(state, action.destination)
            if not marker_ids:
                next_state = legal_actions_module._continue_after_resolved_order(
                    state,
                    british_units=british_units,
                    german_units=state.german_units,
                    unresolved_markers=state.unresolved_markers,
                    rng_state=state.rng_state,
                )
                return V(next_state)

            unresolved_markers = dict(state.unresolved_markers)
            marker_states = tuple(state.unresolved_markers[marker_id] for marker_id in marker_ids)
            marker_probs = tuple(reveal_probs.items())
            total = 0.0
            for marker_assignment in product(marker_probs, repeat=len(marker_ids)):
                probability = 1.0
                german_units = dict(state.german_units)
                unresolved_after_reveal = dict(unresolved_markers)
                for marker_id, marker_state, (unit_class, unit_prob) in zip(
                    marker_ids,
                    marker_states,
                    marker_assignment,
                    strict=True,
                ):
                    probability *= unit_prob
                    unresolved_after_reveal.pop(marker_id)
                    german_units[marker_id] = RevealedGermanUnitState(
                        unit_id=marker_id,
                        unit_class=unit_class,
                        position=marker_state.position,
                        facing=facing_toward_adjacent_hex(
                            marker_state.position, action.destination
                        ),
                        status=GermanUnitStatus.ACTIVE,
                    )
                next_state = legal_actions_module._continue_after_resolved_order(
                    state,
                    british_units=british_units,
                    german_units=german_units,
                    unresolved_markers=unresolved_after_reveal,
                    rng_state=state.rng_state,
                )
                total += probability * V(next_state)
            return total

        if isinstance(action, ScoutAction):
            marker_state = state.unresolved_markers[action.marker_id]
            unresolved_markers = dict(state.unresolved_markers)
            unresolved_markers.pop(action.marker_id)
            total = 0.0
            for unit_class, prob in reveal_probs.items():
                german_units = dict(state.german_units)
                german_units[action.marker_id] = RevealedGermanUnitState(
                    unit_id=action.marker_id,
                    unit_class=unit_class,
                    position=marker_state.position,
                    facing=action.facing,
                    status=GermanUnitStatus.ACTIVE,
                )
                next_state = legal_actions_module._continue_after_resolved_order(
                    state,
                    british_units=state.british_units,
                    german_units=german_units,
                    unresolved_markers=unresolved_markers,
                    rng_state=state.rng_state,
                )
                total += prob * V(next_state)
            return total

        if isinstance(action, (FireAction, GrenadeAttackAction)):
            activation = state.current_activation
            if activation is None:
                raise AssertionError("attack requires current_activation")
            attacker = state.british_units[activation.active_unit_id]
            defender = state.german_units[action.target_unit_id]
            threshold = (
                calculate_fire_threshold(
                    mission,
                    attacker=attacker,
                    defender=defender,
                    british_units=state.british_units,
                )
                if isinstance(action, FireAction)
                else calculate_grenade_attack_threshold(mission, attacker=attacker)
            )
            probability_hit = hit_prob(threshold)
            total = 0.0
            if probability_hit < 1.0:
                next_state = legal_actions_module._continue_after_resolved_order(
                    state,
                    british_units=state.british_units,
                    german_units=state.german_units,
                    unresolved_markers=state.unresolved_markers,
                    rng_state=state.rng_state,
                )
                total += (1.0 - probability_hit) * V(next_state)
            if probability_hit > 0.0:
                german_units = dict(state.german_units)
                german_units[action.target_unit_id] = replace(
                    defender,
                    status=GermanUnitStatus.REMOVED,
                )
                next_state = legal_actions_module._continue_after_resolved_order(
                    state,
                    british_units=state.british_units,
                    german_units=german_units,
                    unresolved_markers=state.unresolved_markers,
                    rng_state=state.rng_state,
                )
                total += probability_hit * V(next_state)
            return total

        if isinstance(action, SelectGermanUnitAction):
            targets = german_fire_target_ids(state, attacker_unit_id=action.unit_id)
            if not targets:
                next_state = replace(
                    state,
                    activated_german_unit_ids=frozenset(
                        (*state.activated_german_unit_ids, action.unit_id)
                    ),
                    pending_decision=ChooseGermanUnitContext(),
                    current_activation=None,
                )
                return V(next_state)
            target_hit_probs = {
                target_id: hit_prob(
                    calculate_german_fire_threshold(
                        state,
                        attacker_unit_id=action.unit_id,
                        target_unit_id=target_id,
                    )
                )
                for target_id in targets
            }
            total = 0.0
            for hit_vector in product([False, True], repeat=len(targets)):
                probability = 1.0
                british_units = dict(state.british_units)
                for target_id, did_hit in zip(targets, hit_vector, strict=True):
                    hit_probability = target_hit_probs[target_id]
                    probability *= hit_probability if did_hit else (1.0 - hit_probability)
                    if did_hit:
                        target = british_units[target_id]
                        british_units[target_id] = replace(
                            target,
                            morale=degrade_british_morale(target.morale),
                        )
                if probability <= 0.0:
                    continue
                next_state = replace(
                    state,
                    british_units=british_units,
                    activated_german_unit_ids=frozenset(
                        (*state.activated_german_unit_ids, action.unit_id)
                    ),
                    pending_decision=ChooseGermanUnitContext(),
                    current_activation=None,
                )
                total += probability * V(next_state)
            return total

        if isinstance(action, ResolveDoubleChoiceAction):
            if action.choice.value == "keep":
                return V(keep_state_with_double(state, state.current_activation.roll[0]))
            return reroll_value(state)

        return V(deterministic_next(state, action))

    def V(raw_state: GameState) -> float:
        nonlocal value_solves
        state, key = normalize_state(raw_state)
        progress_bucket = local_progress_bucket(state)
        cached = cache.get(state.turn, progress_bucket, key)
        if cached is not None:
            return cached

        value_solves += 1
        solved_by_kind[state.pending_decision.kind.value] += 1
        q_entries: list[tuple[GameAction, float]] | None = None
        if state.terminal_outcome is TerminalOutcome.VICTORY:
            value = 1.0
        elif state.terminal_outcome is TerminalOutcome.DEFEAT:
            value = 0.0
        elif on_state_solved is not None:
            q_entries = []
            best_value = -1.0
            for action in get_legal_actions(state):
                q_value = Q(state, action)
                q_entries.append((action, q_value))
                if q_value > best_value:
                    best_value = q_value
            value = best_value
        elif isinstance(state.pending_decision, ChooseDoubleChoiceContext):
            double_value = state.current_activation.roll[0]
            value = max(V(keep_state_with_double(state, double_value)), reroll_value(state))
        else:
            best_value = -1.0
            for action in get_legal_actions(state):
                q_value = Q(state, action)
                if q_value > best_value:
                    best_value = q_value
            value = best_value

        if on_state_solved is not None:
            on_state_solved(state, key, value, q_entries)
        if should_cache_state(state):
            cache.put(state.turn, progress_bucket, key, value)
        maybe_report_progress()
        return value

    def build_policy_engine(pick_action: PickAction):
        policy_values: dict[bytes, float] = {}
        chosen_actions: dict[bytes, GameAction] = {}
        policy_solves = 0
        policy_hits = 0
        policy_started = time.monotonic()
        policy_last_report = policy_started

        def maybe_report_policy_progress(*, force: bool = False) -> None:
            nonlocal policy_last_report
            now = time.monotonic()
            if not force and now - policy_last_report < progress_interval_sec:
                return
            print(
                "[policy] "
                f"elapsed={now - policy_started:.1f}s "
                f"states={len(policy_values)} "
                f"hits={policy_hits} "
                f"solves={policy_solves} "
                f"chosen={len(chosen_actions)}",
                flush=True,
            )
            policy_last_report = now

        def choose_action_for_state(state: GameState, key: bytes) -> GameAction:
            cached_action = chosen_actions.get(key)
            if cached_action is not None:
                return cached_action
            legal_actions = get_legal_actions(state)
            chosen = pick_action(state, legal_actions)
            if chosen not in legal_actions:
                raise ValueError(f"policy returned illegal action {chosen!r} for state {state!r}")
            chosen_actions[key] = chosen
            return chosen

        def reroll_policy_successors(state: GameState) -> tuple[tuple[GameState, float], ...]:
            resolved: dict[bytes, tuple[GameState, float]] = {}
            reroll_probability = 0.0

            def add_successor(raw_state: GameState, probability: float) -> None:
                normalized_state, normalized_key = normalize_state(raw_state)
                existing = resolved.get(normalized_key)
                if existing is None:
                    resolved[normalized_key] = (normalized_state, probability)
                else:
                    resolved[normalized_key] = (existing[0], existing[1] + probability)

            for roll, prob in roll_probs.items():
                if roll[0] == roll[1]:
                    double_state = replace(
                        state,
                        pending_decision=ChooseDoubleChoiceContext(),
                        current_activation=replace(
                            state.current_activation,
                            roll=roll,
                            selected_die=None,
                            planned_orders=(),
                            next_order_index=0,
                        ),
                    )
                    normalized_double_state, double_key = normalize_state(double_state)
                    double_action = choose_action_for_state(normalized_double_state, double_key)
                    if (
                        isinstance(double_action, ResolveDoubleChoiceAction)
                        and double_action.choice.value == "keep"
                    ):
                        add_successor(
                            keep_state_with_double(normalized_double_state, roll[0]), prob
                        )
                    else:
                        reroll_probability += prob
                    continue

                next_state = replace(
                    state,
                    pending_decision=ChooseActivationDieContext(),
                    current_activation=replace(
                        state.current_activation,
                        roll=roll,
                        selected_die=None,
                        planned_orders=(),
                        next_order_index=0,
                    ),
                )
                add_successor(next_state, prob)

            if reroll_probability >= 1.0:
                raise AssertionError("policy reroll loop did not admit any terminating branch")
            if reroll_probability <= 0.0:
                return tuple(resolved.values())
            scale = 1.0 / (1.0 - reroll_probability)
            return tuple(
                (next_state, probability * scale) for next_state, probability in resolved.values()
            )

        def reroll_policy_value(state: GameState) -> float:
            resolved_total = 0.0
            for next_state, prob in reroll_policy_successors(state):
                resolved_total += prob * H(next_state)
            return resolved_total

        def policy_successors(
            raw_state: GameState,
        ) -> tuple[GameState, bytes, GameAction | None, tuple[tuple[GameState, float], ...]]:
            state, key = normalize_state(raw_state)
            if state.terminal_outcome is not None:
                return state, key, None, ()
            chosen = choose_action_for_state(state, key)

            if isinstance(chosen, SelectBritishUnitAction):
                outcomes: dict[bytes, tuple[GameState, float]] = {}
                for roll, prob in roll_probs.items():
                    pending = (
                        ChooseDoubleChoiceContext()
                        if roll[0] == roll[1]
                        else ChooseActivationDieContext()
                    )
                    next_state = replace(
                        state,
                        pending_decision=pending,
                        current_activation=CurrentActivation(
                            active_unit_id=chosen.unit_id, roll=roll
                        ),
                    )
                    normalized_next_state, normalized_next_key = normalize_state(next_state)
                    existing = outcomes.get(normalized_next_key)
                    if existing is None:
                        outcomes[normalized_next_key] = (normalized_next_state, prob)
                    else:
                        outcomes[normalized_next_key] = (existing[0], existing[1] + prob)
                return state, key, chosen, tuple(outcomes.values())

            if isinstance(chosen, AdvanceAction):
                activation = state.current_activation
                if activation is None:
                    raise AssertionError("Advance requires current_activation")
                active_unit = state.british_units[activation.active_unit_id]
                british_units = dict(state.british_units)
                british_units[active_unit.unit_id] = replace(
                    active_unit,
                    position=chosen.destination,
                    cover=0,
                )
                marker_ids = movement_reveal_marker_ids(state, chosen.destination)
                if not marker_ids:
                    next_state = legal_actions_module._continue_after_resolved_order(
                        state,
                        british_units=british_units,
                        german_units=state.german_units,
                        unresolved_markers=state.unresolved_markers,
                        rng_state=state.rng_state,
                    )
                    normalized_next_state, _normalized_next_key = normalize_state(next_state)
                    return state, key, chosen, ((normalized_next_state, 1.0),)

                unresolved_markers = dict(state.unresolved_markers)
                marker_states = tuple(
                    state.unresolved_markers[marker_id] for marker_id in marker_ids
                )
                marker_probs = tuple(reveal_probs.items())
                outcomes: dict[bytes, tuple[GameState, float]] = {}
                for marker_assignment in product(marker_probs, repeat=len(marker_ids)):
                    probability = 1.0
                    german_units = dict(state.german_units)
                    unresolved_after_reveal = dict(unresolved_markers)
                    for marker_id, marker_state, (unit_class, unit_prob) in zip(
                        marker_ids,
                        marker_states,
                        marker_assignment,
                        strict=True,
                    ):
                        probability *= unit_prob
                        unresolved_after_reveal.pop(marker_id)
                        german_units[marker_id] = RevealedGermanUnitState(
                            unit_id=marker_id,
                            unit_class=unit_class,
                            position=marker_state.position,
                            facing=facing_toward_adjacent_hex(
                                marker_state.position, chosen.destination
                            ),
                            status=GermanUnitStatus.ACTIVE,
                        )
                    next_state = legal_actions_module._continue_after_resolved_order(
                        state,
                        british_units=british_units,
                        german_units=german_units,
                        unresolved_markers=unresolved_after_reveal,
                        rng_state=state.rng_state,
                    )
                    normalized_next_state, normalized_next_key = normalize_state(next_state)
                    existing = outcomes.get(normalized_next_key)
                    if existing is None:
                        outcomes[normalized_next_key] = (normalized_next_state, probability)
                    else:
                        outcomes[normalized_next_key] = (existing[0], existing[1] + probability)
                return state, key, chosen, tuple(outcomes.values())

            if isinstance(chosen, ScoutAction):
                marker_state = state.unresolved_markers[chosen.marker_id]
                unresolved_markers = dict(state.unresolved_markers)
                unresolved_markers.pop(chosen.marker_id)
                outcomes: dict[bytes, tuple[GameState, float]] = {}
                for unit_class, prob in reveal_probs.items():
                    german_units = dict(state.german_units)
                    german_units[chosen.marker_id] = RevealedGermanUnitState(
                        unit_id=chosen.marker_id,
                        unit_class=unit_class,
                        position=marker_state.position,
                        facing=chosen.facing,
                        status=GermanUnitStatus.ACTIVE,
                    )
                    next_state = legal_actions_module._continue_after_resolved_order(
                        state,
                        british_units=state.british_units,
                        german_units=german_units,
                        unresolved_markers=unresolved_markers,
                        rng_state=state.rng_state,
                    )
                    normalized_next_state, normalized_next_key = normalize_state(next_state)
                    existing = outcomes.get(normalized_next_key)
                    if existing is None:
                        outcomes[normalized_next_key] = (normalized_next_state, prob)
                    else:
                        outcomes[normalized_next_key] = (existing[0], existing[1] + prob)
                return state, key, chosen, tuple(outcomes.values())

            if isinstance(chosen, (FireAction, GrenadeAttackAction)):
                activation = state.current_activation
                if activation is None:
                    raise AssertionError("attack requires current_activation")
                attacker = state.british_units[activation.active_unit_id]
                defender = state.german_units[chosen.target_unit_id]
                threshold = (
                    calculate_fire_threshold(
                        mission,
                        attacker=attacker,
                        defender=defender,
                        british_units=state.british_units,
                    )
                    if isinstance(chosen, FireAction)
                    else calculate_grenade_attack_threshold(mission, attacker=attacker)
                )
                probability_hit = hit_prob(threshold)
                outcomes: dict[bytes, tuple[GameState, float]] = {}
                if probability_hit < 1.0:
                    next_state = legal_actions_module._continue_after_resolved_order(
                        state,
                        british_units=state.british_units,
                        german_units=state.german_units,
                        unresolved_markers=state.unresolved_markers,
                        rng_state=state.rng_state,
                    )
                    normalized_next_state, normalized_next_key = normalize_state(next_state)
                    current_probability = outcomes.get(
                        normalized_next_key, (normalized_next_state, 0.0)
                    )[1]
                    outcomes[normalized_next_key] = (
                        normalized_next_state,
                        current_probability + (1.0 - probability_hit),
                    )
                if probability_hit > 0.0:
                    german_units = dict(state.german_units)
                    german_units[chosen.target_unit_id] = replace(
                        defender,
                        status=GermanUnitStatus.REMOVED,
                    )
                    next_state = legal_actions_module._continue_after_resolved_order(
                        state,
                        british_units=state.british_units,
                        german_units=german_units,
                        unresolved_markers=state.unresolved_markers,
                        rng_state=state.rng_state,
                    )
                    normalized_next_state, normalized_next_key = normalize_state(next_state)
                    current_probability = outcomes.get(
                        normalized_next_key, (normalized_next_state, 0.0)
                    )[1]
                    outcomes[normalized_next_key] = (
                        normalized_next_state,
                        current_probability + probability_hit,
                    )
                return state, key, chosen, tuple(outcomes.values())

            if isinstance(chosen, SelectGermanUnitAction):
                targets = german_fire_target_ids(state, attacker_unit_id=chosen.unit_id)
                if not targets:
                    next_state = replace(
                        state,
                        activated_german_unit_ids=frozenset(
                            (*state.activated_german_unit_ids, chosen.unit_id)
                        ),
                        pending_decision=ChooseGermanUnitContext(),
                        current_activation=None,
                    )
                    normalized_next_state, _normalized_next_key = normalize_state(next_state)
                    return state, key, chosen, ((normalized_next_state, 1.0),)
                target_hit_probs = {
                    target_id: hit_prob(
                        calculate_german_fire_threshold(
                            state,
                            attacker_unit_id=chosen.unit_id,
                            target_unit_id=target_id,
                        )
                    )
                    for target_id in targets
                }
                outcomes: dict[bytes, tuple[GameState, float]] = {}
                for hit_vector in product([False, True], repeat=len(targets)):
                    probability = 1.0
                    british_units = dict(state.british_units)
                    for target_id, did_hit in zip(targets, hit_vector, strict=True):
                        hit_probability = target_hit_probs[target_id]
                        probability *= hit_probability if did_hit else (1.0 - hit_probability)
                        if did_hit:
                            target = british_units[target_id]
                            british_units[target_id] = replace(
                                target,
                                morale=degrade_british_morale(target.morale),
                            )
                    if probability <= 0.0:
                        continue
                    next_state = replace(
                        state,
                        british_units=british_units,
                        activated_german_unit_ids=frozenset(
                            (*state.activated_german_unit_ids, chosen.unit_id)
                        ),
                        pending_decision=ChooseGermanUnitContext(),
                        current_activation=None,
                    )
                    normalized_next_state, normalized_next_key = normalize_state(next_state)
                    existing = outcomes.get(normalized_next_key)
                    if existing is None:
                        outcomes[normalized_next_key] = (normalized_next_state, probability)
                    else:
                        outcomes[normalized_next_key] = (existing[0], existing[1] + probability)
                return state, key, chosen, tuple(outcomes.values())

            if isinstance(chosen, ResolveDoubleChoiceAction):
                if chosen.choice.value == "keep":
                    normalized_next_state, _normalized_next_key = normalize_state(
                        keep_state_with_double(state, state.current_activation.roll[0]),
                    )
                    return state, key, chosen, ((normalized_next_state, 1.0),)
                return state, key, chosen, reroll_policy_successors(state)

            normalized_next_state, _normalized_next_key = normalize_state(
                deterministic_next(state, chosen)
            )
            return state, key, chosen, ((normalized_next_state, 1.0),)

        def policy_q_value_impl(raw_state: GameState, action: GameAction) -> float:
            state = auto_progress(raw_state)
            if isinstance(action, SelectBritishUnitAction):
                total = 0.0
                for roll, prob in roll_probs.items():
                    pending = (
                        ChooseDoubleChoiceContext()
                        if roll[0] == roll[1]
                        else ChooseActivationDieContext()
                    )
                    next_state = replace(
                        state,
                        pending_decision=pending,
                        current_activation=CurrentActivation(
                            active_unit_id=action.unit_id, roll=roll
                        ),
                    )
                    total += prob * H(next_state)
                return total

            if isinstance(action, AdvanceAction):
                activation = state.current_activation
                if activation is None:
                    raise AssertionError("Advance requires current_activation")
                active_unit = state.british_units[activation.active_unit_id]
                british_units = dict(state.british_units)
                british_units[active_unit.unit_id] = replace(
                    active_unit,
                    position=action.destination,
                    cover=0,
                )
                marker_ids = movement_reveal_marker_ids(state, action.destination)
                if not marker_ids:
                    next_state = legal_actions_module._continue_after_resolved_order(
                        state,
                        british_units=british_units,
                        german_units=state.german_units,
                        unresolved_markers=state.unresolved_markers,
                        rng_state=state.rng_state,
                    )
                    return H(next_state)
                unresolved_markers = dict(state.unresolved_markers)
                marker_states = tuple(
                    state.unresolved_markers[marker_id] for marker_id in marker_ids
                )
                marker_probs = tuple(reveal_probs.items())
                total = 0.0
                for marker_assignment in product(marker_probs, repeat=len(marker_ids)):
                    probability = 1.0
                    german_units = dict(state.german_units)
                    unresolved_after_reveal = dict(unresolved_markers)
                    for marker_id, marker_state, (unit_class, unit_prob) in zip(
                        marker_ids,
                        marker_states,
                        marker_assignment,
                        strict=True,
                    ):
                        probability *= unit_prob
                        unresolved_after_reveal.pop(marker_id)
                        german_units[marker_id] = RevealedGermanUnitState(
                            unit_id=marker_id,
                            unit_class=unit_class,
                            position=marker_state.position,
                            facing=facing_toward_adjacent_hex(
                                marker_state.position, action.destination
                            ),
                            status=GermanUnitStatus.ACTIVE,
                        )
                    next_state = legal_actions_module._continue_after_resolved_order(
                        state,
                        british_units=british_units,
                        german_units=german_units,
                        unresolved_markers=unresolved_after_reveal,
                        rng_state=state.rng_state,
                    )
                    total += probability * H(next_state)
                return total

            if isinstance(action, ScoutAction):
                marker_state = state.unresolved_markers[action.marker_id]
                unresolved_markers = dict(state.unresolved_markers)
                unresolved_markers.pop(action.marker_id)
                total = 0.0
                for unit_class, prob in reveal_probs.items():
                    german_units = dict(state.german_units)
                    german_units[action.marker_id] = RevealedGermanUnitState(
                        unit_id=action.marker_id,
                        unit_class=unit_class,
                        position=marker_state.position,
                        facing=action.facing,
                        status=GermanUnitStatus.ACTIVE,
                    )
                    next_state = legal_actions_module._continue_after_resolved_order(
                        state,
                        british_units=state.british_units,
                        german_units=german_units,
                        unresolved_markers=unresolved_markers,
                        rng_state=state.rng_state,
                    )
                    total += prob * H(next_state)
                return total

            if isinstance(action, (FireAction, GrenadeAttackAction)):
                activation = state.current_activation
                if activation is None:
                    raise AssertionError("attack requires current_activation")
                attacker = state.british_units[activation.active_unit_id]
                defender = state.german_units[action.target_unit_id]
                threshold = (
                    calculate_fire_threshold(
                        mission,
                        attacker=attacker,
                        defender=defender,
                        british_units=state.british_units,
                    )
                    if isinstance(action, FireAction)
                    else calculate_grenade_attack_threshold(mission, attacker=attacker)
                )
                probability_hit = hit_prob(threshold)
                total = 0.0
                if probability_hit < 1.0:
                    next_state = legal_actions_module._continue_after_resolved_order(
                        state,
                        british_units=state.british_units,
                        german_units=state.german_units,
                        unresolved_markers=state.unresolved_markers,
                        rng_state=state.rng_state,
                    )
                    total += (1.0 - probability_hit) * H(next_state)
                if probability_hit > 0.0:
                    german_units = dict(state.german_units)
                    german_units[action.target_unit_id] = replace(
                        defender,
                        status=GermanUnitStatus.REMOVED,
                    )
                    next_state = legal_actions_module._continue_after_resolved_order(
                        state,
                        british_units=state.british_units,
                        german_units=german_units,
                        unresolved_markers=state.unresolved_markers,
                        rng_state=state.rng_state,
                    )
                    total += probability_hit * H(next_state)
                return total

            if isinstance(action, SelectGermanUnitAction):
                targets = german_fire_target_ids(state, attacker_unit_id=action.unit_id)
                if not targets:
                    next_state = replace(
                        state,
                        activated_german_unit_ids=frozenset(
                            (*state.activated_german_unit_ids, action.unit_id)
                        ),
                        pending_decision=ChooseGermanUnitContext(),
                        current_activation=None,
                    )
                    return H(next_state)
                target_hit_probs = {
                    target_id: hit_prob(
                        calculate_german_fire_threshold(
                            state,
                            attacker_unit_id=action.unit_id,
                            target_unit_id=target_id,
                        )
                    )
                    for target_id in targets
                }
                total = 0.0
                for hit_vector in product([False, True], repeat=len(targets)):
                    probability = 1.0
                    british_units = dict(state.british_units)
                    for target_id, did_hit in zip(targets, hit_vector, strict=True):
                        hit_probability = target_hit_probs[target_id]
                        probability *= hit_probability if did_hit else (1.0 - hit_probability)
                        if did_hit:
                            target = british_units[target_id]
                            british_units[target_id] = replace(
                                target,
                                morale=degrade_british_morale(target.morale),
                            )
                    if probability <= 0.0:
                        continue
                    next_state = replace(
                        state,
                        british_units=british_units,
                        activated_german_unit_ids=frozenset(
                            (*state.activated_german_unit_ids, action.unit_id)
                        ),
                        pending_decision=ChooseGermanUnitContext(),
                        current_activation=None,
                    )
                    total += probability * H(next_state)
                return total

            if isinstance(action, ResolveDoubleChoiceAction):
                if action.choice.value == "keep":
                    return H(keep_state_with_double(state, state.current_activation.roll[0]))
                return reroll_policy_value(state)

            return H(deterministic_next(state, action))

        def H(raw_state: GameState) -> float:
            nonlocal policy_solves, policy_hits
            state, key = normalize_state(raw_state)
            cached = policy_values.get(key)
            if cached is not None:
                policy_hits += 1
                return cached
            if state.terminal_outcome is TerminalOutcome.VICTORY:
                policy_solves += 1
                policy_values[key] = 1.0
                maybe_report_policy_progress()
                return 1.0
            if state.terminal_outcome is TerminalOutcome.DEFEAT:
                policy_solves += 1
                policy_values[key] = 0.0
                maybe_report_policy_progress()
                return 0.0
            chosen = choose_action_for_state(state, key)
            policy_solves += 1
            value = policy_q_value_impl(state, chosen)
            policy_values[key] = value
            maybe_report_policy_progress()
            return value

        return (
            H,
            policy_q_value_impl,
            choose_action_for_state,
            policy_successors,
            maybe_report_policy_progress,
        )

    def evaluate_policy(
        pick_action: PickAction,
        *,
        root_raw_state: GameState | None = None,
    ) -> float:
        H, _policy_q_value_impl, _choose_action_for_state, _policy_successors, _progress = (
            build_policy_engine(
                pick_action,
            )
        )
        if root_raw_state is None:
            root_raw_state = create_initial_game_state(mission, seed=0)
        return H(root_raw_state)

    def policy_q_value(
        pick_action: PickAction,
        raw_state: GameState,
        action: GameAction,
    ) -> float:
        _H, policy_q_value_impl, _choose_action_for_state, _policy_successors, _progress = (
            build_policy_engine(
                pick_action,
            )
        )
        return policy_q_value_impl(raw_state, action)

    return ExactPolicySolver(
        mission_path=Path(mission_path),
        codec=codec,
        value=V,
        q_value=Q,
        maybe_report_progress=maybe_report_progress,
        cache=cache,
        normalize_state=normalize_state,
        build_policy_engine=build_policy_engine,
        evaluate_policy=evaluate_policy,
        policy_q_value=policy_q_value,
    )


__all__ = [
    "EXACT_KEY_CODEC_VERSION",
    "EXACT_TIE_TOLERANCE_DEFAULT",
    "ExactPolicySolver",
    "PackedPublicStateCodec",
    "TurnAwareValueCache",
    "action_label",
    "build_capped_exact_policy_solver",
    "current_footprint_bytes",
    "current_rss_bytes",
    "resolve_cap_metric",
]
