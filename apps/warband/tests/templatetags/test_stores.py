import pytest

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.item.models.item import Item
from apps.warband.item.tests.factories.item import ItemFactory
from apps.warband.templatetags.stores import item_upgrade_offer, sell_payout


@pytest.mark.django_db
def test_sell_payout_is_what_selling_the_item_credits():
    faction = FactionFactory(town__marketplace=2)
    item = ItemFactory(savegame=faction.savegame, owner=faction, price=200)

    result = sell_payout(item, faction)

    assert result == 140


@pytest.mark.django_db
def test_item_upgrade_offer_is_what_the_upgrade_view_would_accept():
    faction = FactionFactory(town__weaponsmith=3)
    item = ItemFactory(savegame=faction.savegame, owner=faction, condition=Item.ConditionChoices.CONDITION_RUSTY)

    result = item_upgrade_offer(item=item, faction=faction, month=3, balance=1000)

    assert result["refusal"] is None
