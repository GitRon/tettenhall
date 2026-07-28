import pytest

from apps.town.buildings.base import BuildingEffect
from apps.town.buildings.marketplace import (
    LargeMarketplace,
    Marketplace,
    MediumMarketplace,
    NoMarketplace,
    SmallMarketplace,
)
from apps.town.models import Town


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


def test_get_effects_names_the_resale_share_and_the_stock_size():
    result = SmallMarketplace.get_effects()

    assert result == (
        BuildingEffect(label="Paid when selling an item", value="55% of its price"),
        BuildingEffect(label="Items in the shop", value="4"),
    )
