"""Torch-free masked action-selection helpers for the first learner."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from random import Random


class ActionMaskError(ValueError):
    """Raised when logits and legal-action masks cannot form a valid choice."""


@dataclass(frozen=True, slots=True)
class MaskedActionSelection:
    """One masked action choice with log-probability diagnostics."""

    action_id: int
    log_prob: float
    entropy: float


def select_masked_action(
    logits: Sequence[float],
    legal_action_mask: Sequence[bool],
    *,
    evaluation: bool,
    rng: Random | None = None,
) -> MaskedActionSelection:
    """Choose one legal action id from flat logits and a legal-action mask."""

    if len(logits) != len(legal_action_mask):
        raise ActionMaskError("logits and legal_action_mask must have the same length")

    legal_action_ids = tuple(
        action_id
        for action_id, is_legal in enumerate(legal_action_mask)
        if is_legal
    )
    if not legal_action_ids:
        raise ActionMaskError("legal_action_mask must contain at least one legal action id")

    masked_logits = tuple(float(logits[action_id]) for action_id in legal_action_ids)
    probabilities = _softmax(masked_logits)

    if evaluation:
        selected_index = max(
            range(len(legal_action_ids)),
            key=lambda index: (masked_logits[index], -legal_action_ids[index]),
        )
    else:
        selected_index = _sample_index(probabilities, rng=rng)

    selected_probability = probabilities[selected_index]
    entropy = -sum(
        probability * math.log(probability)
        for probability in probabilities
        if probability > 0.0
    )
    return MaskedActionSelection(
        action_id=legal_action_ids[selected_index],
        log_prob=math.log(selected_probability),
        entropy=entropy,
    )


def _softmax(logits: Sequence[float]) -> tuple[float, ...]:
    max_logit = max(logits)
    shifted = [math.exp(logit - max_logit) for logit in logits]
    total = sum(shifted)
    return tuple(value / total for value in shifted)


def _sample_index(probabilities: Sequence[float], *, rng: Random | None) -> int:
    chooser = Random() if rng is None else rng
    threshold = chooser.random()
    cumulative = 0.0
    for index, probability in enumerate(probabilities):
        cumulative += probability
        if threshold <= cumulative:
            return index
    return len(probabilities) - 1


__all__ = ["ActionMaskError", "MaskedActionSelection", "select_masked_action"]
