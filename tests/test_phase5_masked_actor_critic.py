from __future__ import annotations

from random import Random

from solo_wargame_ai.agents.masked_action_selection import select_masked_action


def test_select_masked_action_never_returns_an_illegal_action_id() -> None:
    logits = (5.0, 1.0, 4.0, 3.0, 2.0)
    legal_action_mask = (False, True, False, True, False)
    rng = Random(7)

    selections = {
        select_masked_action(
            logits,
            legal_action_mask,
            evaluation=False,
            rng=rng,
        ).action_id
        for _ in range(64)
    }

    assert selections == {1, 3}


def test_select_masked_action_uses_the_best_legal_logit_in_evaluation_mode() -> None:
    logits = (9.0, 1.0, 8.0, 1.0)
    legal_action_mask = (False, True, False, True)

    selection = select_masked_action(
        logits,
        legal_action_mask,
        evaluation=True,
    )

    assert selection.action_id == 1
