import pytest

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
