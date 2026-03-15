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
from solo_wargame_ai.env.mission3_action_catalog import (
    Mission3ActionView,
    build_mission3_action_catalog,
)
from solo_wargame_ai.env.mission3_env import Mission3Env
from solo_wargame_ai.io.mission_loader import load_mission

MISSION_PATH = (
    Path(__file__).resolve().parents[1]
    / "configs"
    / "missions"
    / "mission_03_secure_the_building.toml"
)


def test_canonical_mission3_catalog_stays_stable_in_size_and_order() -> None:
    mission = load_mission(MISSION_PATH)

    catalog = build_mission3_action_catalog(mission)

    assert catalog.size == 49
    assert catalog.actions == (
        SelectBritishUnitAction(unit_id="rifle_squad_a"),
        SelectBritishUnitAction(unit_id="rifle_squad_b"),
        SelectBritishUnitAction(unit_id="rifle_squad_c"),
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
        AdvanceAction(destination=HexCoord(q=-2, r=2)),
        AdvanceAction(destination=HexCoord(q=-2, r=3)),
        AdvanceAction(destination=HexCoord(q=-2, r=4)),
        AdvanceAction(destination=HexCoord(q=-1, r=1)),
        AdvanceAction(destination=HexCoord(q=-1, r=2)),
        AdvanceAction(destination=HexCoord(q=-1, r=3)),
        AdvanceAction(destination=HexCoord(q=-1, r=4)),
        AdvanceAction(destination=HexCoord(q=0, r=0)),
        AdvanceAction(destination=HexCoord(q=0, r=1)),
        AdvanceAction(destination=HexCoord(q=0, r=2)),
        AdvanceAction(destination=HexCoord(q=0, r=3)),
        AdvanceAction(destination=HexCoord(q=1, r=0)),
        AdvanceAction(destination=HexCoord(q=1, r=1)),
        AdvanceAction(destination=HexCoord(q=1, r=2)),
        FireAction(target_unit_id="qm_1"),
        FireAction(target_unit_id="qm_2"),
        FireAction(target_unit_id="qm_3"),
        GrenadeAttackAction(target_unit_id="qm_1"),
        GrenadeAttackAction(target_unit_id="qm_2"),
        GrenadeAttackAction(target_unit_id="qm_3"),
        TakeCoverAction(),
        RallyAction(),
        ScoutAction(marker_id="qm_1", facing=HexDirection.DOWN_LEFT),
        ScoutAction(marker_id="qm_1", facing=HexDirection.DOWN),
        ScoutAction(marker_id="qm_1", facing=HexDirection.DOWN_RIGHT),
        ScoutAction(marker_id="qm_2", facing=HexDirection.DOWN_LEFT),
        ScoutAction(marker_id="qm_2", facing=HexDirection.DOWN),
        ScoutAction(marker_id="qm_2", facing=HexDirection.DOWN_RIGHT),
        ScoutAction(marker_id="qm_3", facing=HexDirection.DOWN_LEFT),
        ScoutAction(marker_id="qm_3", facing=HexDirection.DOWN),
        SelectGermanUnitAction(unit_id="qm_1"),
        SelectGermanUnitAction(unit_id="qm_2"),
        SelectGermanUnitAction(unit_id="qm_3"),
    )


def test_catalog_encode_decode_round_trips_every_action_id() -> None:
    mission = load_mission(MISSION_PATH)

    catalog = build_mission3_action_catalog(mission)

    for action_id, action in enumerate(catalog.actions):
        assert catalog.encode(action) == action_id
        assert catalog.decode(action_id) == action


def test_public_mission3_action_catalog_uses_opaque_contact_handles_in_stable_slots() -> None:
    mission = load_mission(MISSION_PATH)

    catalog = Mission3Env(mission).action_catalog

    assert catalog.size == 49
    assert catalog.decode(0) == Mission3ActionView(
        kind="select_british_unit",
        unit_id="rifle_squad_a",
    )
    assert catalog.decode(30) == Mission3ActionView(kind="fire", contact_id="contact_0")
    assert catalog.decode(31) == Mission3ActionView(kind="fire", contact_id="contact_1")
    assert catalog.decode(32) == Mission3ActionView(kind="fire", contact_id="contact_2")
    assert catalog.decode(33) == Mission3ActionView(
        kind="grenade_attack",
        contact_id="contact_0",
    )
    assert catalog.decode(38) == Mission3ActionView(
        kind="scout",
        contact_id="contact_0",
        facing="down_left",
    )
    assert catalog.decode(41) == Mission3ActionView(
        kind="scout",
        contact_id="contact_1",
        facing="down_left",
    )
    assert catalog.decode(46) == Mission3ActionView(
        kind="select_german_unit",
        contact_id="contact_0",
    )
    assert catalog.decode(48) == Mission3ActionView(
        kind="select_german_unit",
        contact_id="contact_2",
    )

    for action_id, action in enumerate(catalog.actions):
        assert catalog.encode(action) == action_id
        _assert_no_raw_qm_strings(action)


def _assert_no_raw_qm_strings(action: Mission3ActionView) -> None:
    for value in (
        action.kind,
        action.unit_id,
        action.contact_id,
        action.choice,
        action.facing,
    ):
        if value is not None:
            assert not value.startswith("qm_")
