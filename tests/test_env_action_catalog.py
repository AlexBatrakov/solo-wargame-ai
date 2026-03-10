from __future__ import annotations

from pathlib import Path

from solo_wargame_ai.domain.actions import (
    AdvanceAction,
    ChooseOrderExecutionAction,
    DiscardActivationRollAction,
    DoubleChoiceOption,
    FireAction,
    GrenadeAttackAction,
    OrderExecutionChoice,
    RallyAction,
    ResolveDoubleChoiceAction,
    ScoutAction,
    SelectActivationDieAction,
    SelectBritishUnitAction,
    SelectGermanUnitAction,
    TakeCoverAction,
)
from solo_wargame_ai.domain.enums import HexDirection
from solo_wargame_ai.domain.hexgrid import HexCoord
from solo_wargame_ai.env.action_catalog import build_mission1_action_catalog
from solo_wargame_ai.io.mission_loader import load_mission

MISSION_PATH = (
    Path(__file__).resolve().parents[1]
    / "configs"
    / "missions"
    / "mission_01_secure_the_woods_1.toml"
)


def test_canonical_mission1_catalog_stays_stable_in_size_and_order() -> None:
    mission = load_mission(MISSION_PATH)

    catalog = build_mission1_action_catalog(mission)

    assert catalog.size == 32
    assert catalog.actions == (
        SelectBritishUnitAction(unit_id="rifle_squad_a"),
        SelectBritishUnitAction(unit_id="rifle_squad_b"),
        ResolveDoubleChoiceAction(choice=DoubleChoiceOption.KEEP),
        ResolveDoubleChoiceAction(choice=DoubleChoiceOption.REROLL),
        SelectActivationDieAction(die_value=1),
        SelectActivationDieAction(die_value=2),
        SelectActivationDieAction(die_value=3),
        SelectActivationDieAction(die_value=4),
        SelectActivationDieAction(die_value=5),
        SelectActivationDieAction(die_value=6),
        DiscardActivationRollAction(),
        ChooseOrderExecutionAction(choice=OrderExecutionChoice.FIRST_ORDER_ONLY),
        ChooseOrderExecutionAction(choice=OrderExecutionChoice.SECOND_ORDER_ONLY),
        ChooseOrderExecutionAction(choice=OrderExecutionChoice.BOTH_ORDERS),
        ChooseOrderExecutionAction(choice=OrderExecutionChoice.NO_ACTION),
        AdvanceAction(destination=HexCoord(q=-1, r=1)),
        AdvanceAction(destination=HexCoord(q=-1, r=2)),
        AdvanceAction(destination=HexCoord(q=-1, r=3)),
        AdvanceAction(destination=HexCoord(q=0, r=0)),
        AdvanceAction(destination=HexCoord(q=0, r=1)),
        AdvanceAction(destination=HexCoord(q=0, r=2)),
        AdvanceAction(destination=HexCoord(q=1, r=0)),
        AdvanceAction(destination=HexCoord(q=1, r=1)),
        AdvanceAction(destination=HexCoord(q=1, r=2)),
        FireAction(target_unit_id="qm_1"),
        GrenadeAttackAction(target_unit_id="qm_1"),
        TakeCoverAction(),
        RallyAction(),
        ScoutAction(marker_id="qm_1", facing=HexDirection.DOWN_LEFT),
        ScoutAction(marker_id="qm_1", facing=HexDirection.DOWN),
        ScoutAction(marker_id="qm_1", facing=HexDirection.DOWN_RIGHT),
        SelectGermanUnitAction(unit_id="qm_1"),
    )


def test_catalog_encode_decode_round_trips_every_action_id() -> None:
    mission = load_mission(MISSION_PATH)

    catalog = build_mission1_action_catalog(mission)

    for action_id, action in enumerate(catalog.actions):
        assert catalog.encode(action) == action_id
        assert catalog.decode(action_id) == action
