import pytest

from apps.warband.faction.services.hiring import UNAFFORDABLE_REFUSAL, get_pub_hire_refusal
from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.finance.tests.factories.transaction import TransactionFactory


@pytest.mark.django_db
def test_get_pub_hire_refusal_lets_a_faction_hire_a_man_it_can_pay_for():
    faction = FactionFactory()
    TransactionFactory(faction=faction, amount=180)

    assert get_pub_hire_refusal(faction=faction, hiring_price=180) is None


@pytest.mark.django_db
def test_get_pub_hire_refusal_refuses_a_man_dearer_than_the_purse():
    faction = FactionFactory()
    TransactionFactory(faction=faction, amount=179)

    assert get_pub_hire_refusal(faction=faction, hiring_price=180) == UNAFFORDABLE_REFUSAL
