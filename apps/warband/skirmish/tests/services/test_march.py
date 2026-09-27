import pytest

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.finance.tests.factories.transaction import TransactionFactory
from apps.warband.skirmish.services.march import get_march_cost_refusal


@pytest.mark.django_db
def test_get_march_cost_refusal_in_summer():
    """A free month needs no purse at all."""
    faction = FactionFactory()

    assert get_march_cost_refusal(faction_id=faction.id, month=3, warrior_count=5) is None


@pytest.mark.django_db
def test_get_march_cost_refusal_in_winter_with_the_silver():
    faction = FactionFactory()
    TransactionFactory(faction=faction, amount=50)

    assert get_march_cost_refusal(faction_id=faction.id, month=7, warrior_count=5) is None


@pytest.mark.django_db
def test_get_march_cost_refusal_in_winter_without_the_silver():
    faction = FactionFactory()
    TransactionFactory(faction=faction, amount=49)

    result = get_march_cost_refusal(faction_id=faction.id, month=7, warrior_count=5)

    assert result == "Marching 5 men this month costs 50 silver, and you have 49."
