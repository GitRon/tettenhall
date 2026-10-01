from apps.common.tests.html import parse, render_component
from apps.warband.item.models.item import Item
from apps.warband.item.models.item_type import ItemType
from apps.warband.item.tests.factories.item import ItemFactory
from apps.warband.item.tests.factories.item_type import ItemTypeFactory

STATS_META_TAG = '<c-item.stats-meta :item="item" />'


def _item(*, function: int = ItemType.FunctionChoices.FUNCTION_WEAPON, dice: str = "1d6", modifier: int = 1) -> Item:
    return ItemFactory.build(
        price=40, modifier=modifier, type=ItemTypeFactory.build(function=function, base_value=dice)
    )


def _text(html: str) -> str:
    return " ".join(parse(html).get_text(" ").split())


def test_stats_meta_gives_a_weapon_its_damage_roll_and_average():
    html = render_component(tag=STATS_META_TAG, context={"item": _item()})

    result = _text(html)

    assert result == "Damage 1d6+1 Average 4.5"


def test_stats_meta_gives_armour_its_protection_roll():
    html = render_component(
        tag=STATS_META_TAG, context={"item": _item(function=ItemType.FunctionChoices.FUNCTION_ARMOR)}
    )

    result = _text(html)

    assert result == "Protection 1d6+1 Average 4.5"


def test_stats_meta_trims_a_whole_average():
    html = render_component(tag=STATS_META_TAG, context={"item": _item(dice="2d6", modifier=0)})

    result = _text(html)

    assert result == "Damage 2d6+0 Average 7"


def test_stats_meta_names_the_price_only_when_asked():
    html = render_component(tag='<c-item.stats-meta :item="item" show_price />', context={"item": _item()})

    result = _text(html)

    assert result == "40 silver Damage 1d6+1 Average 4.5"
