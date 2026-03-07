"""Deterministic RNG wrapper used by the simulator."""

from __future__ import annotations

from dataclasses import dataclass
from random import Random
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class RNGState:
    """Serializable snapshot of the wrapped RNG state."""

    seed: int | None
    version: int
    internal_state: tuple[int, ...]
    gauss_next: float | None

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly representation of this state snapshot."""

        return {
            "seed": self.seed,
            "version": self.version,
            "internal_state": list(self.internal_state),
            "gauss_next": self.gauss_next,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "RNGState":
        """Rebuild a state snapshot previously created by :meth:`to_dict`."""

        return cls(
            seed=data["seed"],
            version=int(data["version"]),
            internal_state=tuple(int(value) for value in data["internal_state"]),
            gauss_next=data["gauss_next"],
        )


class DeterministicRNG:
    """Project-controlled wrapper around :class:`random.Random`."""

    def __init__(self, seed: int | None = None) -> None:
        self._seed = seed
        self._random = Random(seed)

    @property
    def seed(self) -> int | None:
        """Return the original seed used to initialize this RNG."""

        return self._seed

    def randint(self, lower: int, upper: int) -> int:
        """Return an inclusive random integer."""

        return self._random.randint(lower, upper)

    def roll_d6(self) -> int:
        """Roll one six-sided die."""

        return self.randint(1, 6)

    def roll_nd6(self, count: int) -> tuple[int, ...]:
        """Roll ``count`` six-sided dice."""

        if count < 0:
            raise ValueError("count must be non-negative")

        return tuple(self.roll_d6() for _ in range(count))

    def snapshot(self) -> RNGState:
        """Capture the current RNG state in a serializable form."""

        version, internal_state, gauss_next = self._random.getstate()
        return RNGState(
            seed=self._seed,
            version=version,
            internal_state=tuple(internal_state),
            gauss_next=gauss_next,
        )

    def restore(self, state: RNGState) -> None:
        """Restore the RNG to a previously captured snapshot."""

        self._seed = state.seed
        self._random.setstate((state.version, state.internal_state, state.gauss_next))

    @classmethod
    def from_state(cls, state: RNGState) -> "DeterministicRNG":
        """Construct an RNG directly from a serialized snapshot."""

        rng = cls(seed=state.seed)
        rng.restore(state)
        return rng


__all__ = ["DeterministicRNG", "RNGState"]
