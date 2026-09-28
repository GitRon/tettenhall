import pytest

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.item.tests.factories.item import ItemFactory
from apps.warband.templatetags.stores import sell_payout


@pytest.mark.django_db
def test_sell_payout_is_what_selling_the_item_credits():
    faction = FactionFactory(town__marketplace=2)
    item = ItemFactory(savegame=faction.savegame, owner=faction, price=200)

    result = sell_payout(item, faction)

    assert result == 140
