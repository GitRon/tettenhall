import pytest

from apps.item.models.item_type import ItemType
from apps.item.tests.factories.item import ItemFactory
from apps.item.tests.factories.item_type import ItemTypeFactory
from apps.skirmish.models.warrior import Warrior
from apps.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_replenish_current_health_caps_at_the_maximum():
    warrior = WarriorFactory(current_health=18, max_health=20)

    result = Warrior.objects.replenish_current_health(obj=warrior, healed_points=10)

    assert result.current_health == 20


@pytest.mark.django_db
def test_replenish_current_health_keeps_a_warrior_still_below_zero_unconscious():
    warrior = WarriorFactory(
        current_health=-10, max_health=20, condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS
    )

    result = Warrior.objects.replenish_current_health(obj=warrior, healed_points=5)

    assert result.current_health == -5
    assert result.condition == Warrior.ConditionChoices.CONDITION_UNCONSCIOUS


@pytest.mark.django_db
def test_take_item_away_unequips_the_weapon():
    weapon = ItemFactory(type=ItemTypeFactory(function=ItemType.FunctionChoices.FUNCTION_WEAPON))
    warrior = WarriorFactory(weapon=weapon)

    Warrior.objects.take_item_away(item=weapon)

    warrior.refresh_from_db()
    assert warrior.weapon is None


@pytest.mark.django_db
def test_take_item_away_unequips_the_armor():
    armor = ItemFactory(type=ItemTypeFactory(function=ItemType.FunctionChoices.FUNCTION_ARMOR))
    warrior = WarriorFactory(armor=armor)

    Warrior.objects.take_item_away(item=armor)

    warrior.refresh_from_db()
    assert warrior.armor is None


@pytest.mark.django_db
def test_replenish_current_morale_caps_at_the_maximum():
    warrior = WarriorFactory(current_morale=18, max_morale=20)

    result = Warrior.objects.replenish_current_morale(obj=warrior, recovered_morale_points=10)

    assert result.current_morale == 20


@pytest.mark.django_db
def test_increase_morale_adds_the_gained_points():
    warrior = WarriorFactory(current_morale=10, max_morale=20)

    result = Warrior.objects.increase_morale(obj=warrior, increased_morale=5)

    assert result.current_morale == 15


@pytest.mark.django_db
def test_increase_morale_caps_at_the_maximum():
    warrior = WarriorFactory(current_morale=18, max_morale=20)

    result = Warrior.objects.increase_morale(obj=warrior, increased_morale=5)

    assert result.current_morale == 20


@pytest.mark.django_db
def test_increase_experience_adds_the_gained_points():
    warrior = WarriorFactory(experience=100)

    result = Warrior.objects.increase_experience(obj=warrior, experience=25)

    assert result.experience == 125
