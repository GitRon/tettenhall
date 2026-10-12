from apps.common.tests.html import parse, render_component
from apps.warband.item.tests.factories.item import ItemFactory
from apps.warband.item.tests.factories.item_type import ItemTypeFactory

ROSTER_GEAR_TAG = '<c-warrior.roster-gear :item="item" />'


def _text(html: str) -> str:
    return " ".join(parse(html).get_text(" ").split())


def test_roster_gear_names_the_item_and_its_roll():
    item = ItemFactory.build(modifier=1, type=ItemTypeFactory.build(name="Seax", base_value="1d6"))
    html = render_component(tag=ROSTER_GEAR_TAG, context={"item": item})

    result = _text(html)

    assert result == f"{item.display_name} 1d6+1 · 4.5"


def test_roster_gear_average_counts_a_blow_below_nothing_as_nothing():
    """
    A quarter, at the one decimal every average in the game is printed to - not the -0.5 the unfloored
    arithmetic gives.
    """
    item = ItemFactory.build(modifier=-3, type=ItemTypeFactory.build(name="Rusty Pitchfork", base_value="1d4"))
    html = render_component(tag=ROSTER_GEAR_TAG, context={"item": item})

    result = _text(html)

    assert result == f"{item.display_name} 1d4-3 · 0.3"


def test_roster_gear_empty_slot_is_a_dash():
    html = render_component(tag=ROSTER_GEAR_TAG, context={"item": None})

    result = _text(html)

    assert result == "—"
