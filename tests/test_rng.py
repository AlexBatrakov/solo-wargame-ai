from solo_wargame_ai.domain.rng import DeterministicRNG, RNGState


def test_same_seed_produces_same_roll_sequence() -> None:
    first_rng = DeterministicRNG(seed=1729)
    second_rng = DeterministicRNG(seed=1729)

    assert first_rng.roll_nd6(8) == second_rng.roll_nd6(8)


def test_snapshot_and_restore_replay_the_same_future_sequence() -> None:
    rng = DeterministicRNG(seed=7)

    rng.roll_d6()
    snapshot = rng.snapshot()
    expected_future = rng.roll_nd6(5)

    rng.restore(snapshot)

    assert rng.roll_nd6(5) == expected_future


def test_serialized_state_round_trips() -> None:
    rng = DeterministicRNG(seed=99)
    rng.roll_nd6(4)

    serialized_state = rng.snapshot().to_dict()
    restored_state = RNGState.from_dict(serialized_state)
    restored_rng = DeterministicRNG.from_state(restored_state)

    assert restored_rng.seed == 99
    assert restored_rng.roll_nd6(6) == rng.roll_nd6(6)


def test_roll_nd6_rejects_negative_counts() -> None:
    rng = DeterministicRNG(seed=1)

    try:
        rng.roll_nd6(-1)
    except ValueError as exc:
        assert str(exc) == "count must be non-negative"
    else:
        raise AssertionError("Expected roll_nd6 to reject negative counts")
