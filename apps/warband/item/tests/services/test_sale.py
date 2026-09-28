import pytest

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.item.services.sale import get_sell_payout
from apps.warband.item.tests.factories.item import ItemFactory
from apps.warband.town.models import Town


@pytest.mark.django_db
def test_get_sell_payout_without_a_market_of_its_own():
    faction = FactionFactory()
    item = ItemFactory(savegame=faction.savegame, owner=faction, price=90)

    assert get_sell_payout(item=item, faction=faction) == 36


@pytest.mark.django_db
def test_get_sell_payout_follows_the_town_s_current_marketplace():
    faction = FactionFactory()
    item = ItemFactory(savegame=faction.savegame, owner=faction, price=90)
    faction.town.marketplace = Town.MarketChoices.MARKET_LARGE
    faction.town.save()

    assert get_sell_payout(item=item, faction=faction) == 76
