import pytest

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.finance.tests.factories.transaction import TransactionFactory
from apps.warband.item.services.purchase import UNAFFORDABLE_REFUSAL, get_purchase_refusal
from apps.warband.item.tests.factories.item import ItemFactory


@pytest.mark.django_db
def test_get_purchase_refusal_lets_a_faction_buy_what_it_can_pay_for():
    faction = FactionFactory()
    TransactionFactory(faction=faction, amount=200)
    item = ItemFactory(savegame=faction.savegame, owner=None, price=200)

    assert get_purchase_refusal(item=item, faction=faction) is None


@pytest.mark.django_db
def test_get_purchase_refusal_refuses_an_item_dearer_than_the_purse():
    faction = FactionFactory()
    TransactionFactory(faction=faction, amount=199)
    item = ItemFactory(savegame=faction.savegame, owner=None, price=200)

    assert get_purchase_refusal(item=item, faction=faction) == UNAFFORDABLE_REFUSAL
