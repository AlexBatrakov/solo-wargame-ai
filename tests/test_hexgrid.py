from solo_wargame_ai.domain.enums import HexDirection
from solo_wargame_ai.domain.hexgrid import (
    ALL_DIRECTIONS,
    AXIAL_DIRECTION_DELTAS,
    BRITISH_FORWARD_DIRECTIONS,
    HexCoord,
    are_adjacent,
    british_forward_neighbors,
    neighbor,
    neighbors,
)


def test_axial_direction_deltas_match_documented_flat_top_convention() -> None:
    assert AXIAL_DIRECTION_DELTAS[HexDirection.UP_LEFT] == HexCoord(-1, 0)
    assert AXIAL_DIRECTION_DELTAS[HexDirection.UP] == HexCoord(0, -1)
    assert AXIAL_DIRECTION_DELTAS[HexDirection.UP_RIGHT] == HexCoord(1, -1)
    assert AXIAL_DIRECTION_DELTAS[HexDirection.DOWN_RIGHT] == HexCoord(1, 0)
    assert AXIAL_DIRECTION_DELTAS[HexDirection.DOWN] == HexCoord(0, 1)
    assert AXIAL_DIRECTION_DELTAS[HexDirection.DOWN_LEFT] == HexCoord(-1, 1)


def test_neighbors_follow_direction_order() -> None:
    origin = HexCoord(0, 0)

    assert ALL_DIRECTIONS == (
        HexDirection.UP_LEFT,
        HexDirection.UP,
        HexDirection.UP_RIGHT,
        HexDirection.DOWN_RIGHT,
        HexDirection.DOWN,
        HexDirection.DOWN_LEFT,
    )
    assert neighbors(origin) == (
        HexCoord(-1, 0),
        HexCoord(0, -1),
        HexCoord(1, -1),
        HexCoord(1, 0),
        HexCoord(0, 1),
        HexCoord(-1, 1),
    )


def test_are_adjacent_matches_axial_neighbors() -> None:
    origin = HexCoord(0, 1)

    assert are_adjacent(origin, neighbor(origin, HexDirection.UP_RIGHT))
    assert are_adjacent(origin, neighbor(origin, HexDirection.DOWN_LEFT))
    assert not are_adjacent(origin, HexCoord(2, 1))
    assert not are_adjacent(origin, origin)


def test_british_forward_neighbors_use_documented_default_directions() -> None:
    origin = HexCoord(0, 3)

    assert BRITISH_FORWARD_DIRECTIONS == (
        HexDirection.UP_LEFT,
        HexDirection.UP,
        HexDirection.UP_RIGHT,
    )
    assert british_forward_neighbors(origin) == (
        HexCoord(-1, 3),
        HexCoord(0, 2),
        HexCoord(1, 2),
    )


def test_british_forward_neighbors_respect_supplied_forward_directions() -> None:
    origin = HexCoord(0, 0)
    forward_directions = (HexDirection.DOWN_RIGHT, HexDirection.DOWN)

    assert british_forward_neighbors(origin, forward_directions=forward_directions) == (
        HexCoord(1, 0),
        HexCoord(0, 1),
    )
