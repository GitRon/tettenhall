import pytest

from apps.faction.tests.factories.faction import FactionFactory
from apps.item.models.item_type import ItemType
from apps.item.tests.factories.item import ItemFactory
from apps.item.tests.factories.item_type import ItemTypeFactory
from apps.quest.tests.factories.quest_contract import QuestContractFactory
from apps.skirmish.models.warrior import Warrior
from apps.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_exclude_currently_busy_keeps_a_warrior_who_has_never_fought():
    warrior = WarriorFactory()

    result = Warrior.objects.exclude_currently_busy(month=3)

    assert list(result) == [warrior]


@pytest.mark.django_db
def test_exclude_currently_busy_drops_a_warrior_on_a_quest():
    warrior = WarriorFactory()
    quest_contract = QuestContractFactory(faction=warrior.faction, accepted_in_month=3)
    quest_contract.assigned_warriors.add(warrior)

    result = Warrior.objects.exclude_currently_busy(month=3)

    assert list(result) == []


@pytest.mark.django_db
def test_exclude_currently_busy_drops_a_warrior_holding_an_older_contract_too():
    """
    Read per joined contract rather than per warrior, the older row satisfied "this one is not the
    month asked about" and handed him back as free.
    """
    warrior = WarriorFactory()
    for accepted_month in (1, 3):
        quest_contract = QuestContractFactory(faction=warrior.faction, accepted_in_month=accepted_month)
        quest_contract.assigned_warriors.add(warrior)

    result = Warrior.objects.exclude_currently_busy(month=3)

    assert list(result) == []


@pytest.mark.django_db
def test_exclude_currently_busy_keeps_a_warrior_whose_only_quest_was_last_month():
    warrior = WarriorFactory()
    quest_contract = QuestContractFactory(faction=warrior.faction, accepted_in_month=2)
    quest_contract.assigned_warriors.add(warrior)

    result = Warrior.objects.exclude_currently_busy(month=3)

    assert list(result) == [warrior]


@pytest.mark.django_db
def test_exclude_currently_busy_drops_a_warrior_who_fought_this_month():
    """
    Every warrior fights once a month, so a decided fight still uses the month up.
    """
    warrior = WarriorFactory()
    skirmish = SkirmishFactory(attacking_faction=warrior.faction, victorious_faction=warrior.faction, month=3)
    skirmish.attacking_warriors.add(warrior)

    result = Warrior.objects.exclude_currently_busy(month=3)

    assert list(result) == []


@pytest.mark.django_db
def test_exclude_currently_busy_drops_a_warrior_still_in_an_undecided_fight():
    """
    An unresolved fight carries over, and the month check alone would hand the same warrior out
    again next month while he is still standing on that roster.
    """
    warrior = WarriorFactory()
    skirmish = SkirmishFactory(attacking_faction=warrior.faction, month=2)
    skirmish.attacking_warriors.add(warrior)

    result = Warrior.objects.exclude_currently_busy(month=3)

    assert list(result) == []


@pytest.mark.django_db
def test_exclude_currently_busy_keeps_a_warrior_whose_last_fight_is_over():
    warrior = WarriorFactory()
    skirmish = SkirmishFactory(attacking_faction=warrior.faction, victorious_faction=warrior.faction, month=2)
    skirmish.attacking_warriors.add(warrior)

    result = Warrior.objects.exclude_currently_busy(month=3)

    assert list(result) == [warrior]


@pytest.mark.django_db
def test_exclude_currently_busy_drops_a_warrior_who_fought_on_the_defending_side():
    """
    Which side of the row a warrior stands on is a property of the skirmish, not of him - a captive
    who has since changed banners fought all the same.
    """
    warrior = WarriorFactory()
    skirmish = SkirmishFactory(
        defending_faction=warrior.faction,
        attacking_faction=FactionFactory(savegame=warrior.savegame),
        victorious_faction=warrior.faction,
        month=3,
    )
    skirmish.defending_warriors.add(warrior)

    result = Warrior.objects.exclude_currently_busy(month=3)

    assert list(result) == []


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


@pytest.mark.django_db
def test_apply_level_up_growth_takes_a_tenth_of_every_grown_value():
    warrior = WarriorFactory(strength=10, dexterity=10, max_health=20, max_morale=20, monthly_salary=150)

    result = Warrior.objects.apply_level_up_growth(obj=warrior)

    assert result == {"strength": 1, "dexterity": 1, "max_health": 2, "max_morale": 2, "monthly_salary": 15}
    warrior.refresh_from_db()
    assert (warrior.strength, warrior.dexterity, warrior.max_health, warrior.max_morale, warrior.monthly_salary) == (
        11,
        11,
        22,
        22,
        165,
    )


@pytest.mark.django_db
def test_apply_level_up_growth_floors_every_gain_at_one_point():
    """
    A levy off the fyrd sits at about five strength, five dexterity and five morale, and a tenth of
    five rounds to zero - Python rounds halves to even. Without the floor he would level up, gain a
    single hit point off his larger health pool, and charge more for it.
    """
    warrior = WarriorFactory(strength=5, dexterity=5, max_health=10, max_morale=5, monthly_salary=150)

    result = Warrior.objects.apply_level_up_growth(obj=warrior)

    assert result == {"strength": 1, "dexterity": 1, "max_health": 1, "max_morale": 1, "monthly_salary": 15}


@pytest.mark.django_db
def test_apply_level_up_growth_leaves_the_current_values_alone():
    """
    Experience arrives during a skirmish, so raising current_health along with the maximum would top a
    warrior up mid-battle and make winning harder the cheapest way to survive a fight.
    """
    warrior = WarriorFactory(current_health=5, max_health=20, current_morale=5, max_morale=20, monthly_salary=150)

    Warrior.objects.apply_level_up_growth(obj=warrior)

    warrior.refresh_from_db()
    assert (warrior.current_health, warrior.current_morale) == (5, 5)
