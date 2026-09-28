import pytest

from apps.warband.town.buildings.base import BuildingEffect
from apps.warband.town.buildings.marketplace import (
    LargeMarketplace,
    Marketplace,
    MediumMarketplace,
    NoMarketplace,
    SmallMarketplace,
)
from apps.warband.town.models import Town


def test_get_building_by_type_without_a_marketplace():
    result = Marketplace.get_building_by_type(building_type=Town.MarketChoices.MARKET_NONE)

    assert isinstance(result, NoMarketplace)


def test_get_building_by_type_small():
    result = Marketplace.get_building_by_type(building_type=Town.MarketChoices.MARKET_SMALL)

    assert isinstance(result, SmallMarketplace)


def test_get_building_by_type_medium():
    result = Marketplace.get_building_by_type(building_type=Town.MarketChoices.MARKET_MEDIUM)

    assert isinstance(result, MediumMarketplace)


def test_get_building_by_type_large():
    result = Marketplace.get_building_by_type(building_type=Town.MarketChoices.MARKET_LARGE)

    assert isinstance(result, LargeMarketplace)


def test_get_building_by_type_unknown_level():
    with pytest.raises(RuntimeError, match="Unknown marketplace type: 4"):
        Marketplace.get_building_by_type(building_type=4)


def test_get_levels_matches_the_model_choices():
    """
    The level is written straight into a choices-constrained column and Django validates choices only
    in forms, so a variant added here without its counterpart on the model would store a level the
    display and the admin cannot handle.
    """
    assert len(Marketplace.get_levels()) == len(Town.MarketChoices)


@pytest.mark.parametrize(
    ("marketplace", "expected"),
    [(NoMarketplace, 36), (SmallMarketplace, 49), (MediumMarketplace, 63), (LargeMarketplace, 76)],
)
def test_get_sell_payout_pays_the_level_s_share_of_the_list_price(marketplace, expected):
    assert marketplace.get_sell_payout(price=90) == expected


def test_get_sell_payout_rounds_a_half_share_down():
    """
    110 at 55% is exactly 60.5. In floats it comes out as 60.500000000000004, which would round up to
    61 while 90 at 85% (exactly 76.5) rounds down - so the share is taken in whole silver.
    """
    assert SmallMarketplace.get_sell_payout(price=110) == 60


def test_get_sell_payout_pays_at_least_a_silver():
    assert NoMarketplace.get_sell_payout(price=1) == 1


def test_get_effects_names_the_resale_share_and_the_stock_size():
    result = SmallMarketplace.get_effects()

    assert result == (
        BuildingEffect(label="Paid when selling an item", value="55% of its price"),
        BuildingEffect(label="Items in the shop", value="4"),
    )
