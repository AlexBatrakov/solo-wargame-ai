import pytest

from solo_wargame_ai.domain.terrain import TerrainType, is_terrain_name, terrain_from_name


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("clear", TerrainType.CLEAR),
        ("woods", TerrainType.WOODS),
        ("building", TerrainType.BUILDING),
        ("hill", TerrainType.HILL),
        ("river", TerrainType.RIVER),
    ],
)
def test_terrain_from_name_accepts_supported_values(
    name: str,
    expected: TerrainType,
) -> None:
    assert terrain_from_name(name) is expected
    assert is_terrain_name(name)


def test_terrain_from_name_rejects_unknown_values() -> None:
    with pytest.raises(ValueError, match="Unknown terrain type: bog"):
        terrain_from_name("bog")

    assert not is_terrain_name("bog")
