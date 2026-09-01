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
def test_in_pub_of_returns_the_mercenaries_of_that_pub():
    faction = FactionFactory()
    mercenary = WarriorFactory(faction=None, savegame=faction.savegame, culture=faction.culture)
    faction.available_mercenaries.add(mercenary)

    result = Warrior.objects.in_pub_of(faction_id=faction.id)

    assert list(result) == [mercenary]


@pytest.mark.django_db
def test_in_pub_of_leaves_out_another_factions_pub():
    faction = FactionFactory()
    other_faction = FactionFactory(savegame=faction.savegame)
    mercenary = WarriorFactory(faction=None, savegame=faction.savegame, culture=faction.culture)
    other_faction.available_mercenaries.add(mercenary)

    result = Warrior.objects.in_pub_of(faction_id=faction.id)

    assert list(result) == []


@pytest.mark.django_db
def test_in_pub_of_leaves_out_a_warrior_who_is_merely_factionless():
    """
    A deserter and a captive whose banner was cleared have no faction either, and neither is standing
    in the pub - membership is what this asks about, not a missing faction.
    """
    faction = FactionFactory()
    WarriorFactory(faction=None, savegame=faction.savegame, culture=faction.culture)

    result = Warrior.objects.in_pub_of(faction_id=faction.id)

    assert list(result) == []


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
def test_reduce_current_health_subtracts_the_damage():
    warrior = WarriorFactory(current_health=18, max_health=20)

    result = Warrior.objects.reduce_current_health(obj=warrior, damage=5)

    assert result.current_health == 13


@pytest.mark.django_db
def test_reduce_current_health_keeps_the_overkill_of_a_fatal_blow():
    """
    Unfloored on purpose: how far past zero the blow carried him is what tells a corpse from a
    captive, and "put_out_of_the_fight" is what tidies the number away afterwards.
    """
    warrior = WarriorFactory(current_health=4, max_health=20)

    result = Warrior.objects.reduce_current_health(obj=warrior, damage=15)

    assert result.current_health == -11


@pytest.mark.django_db
def test_put_out_of_the_fight_floors_health_at_nothing():
    warrior = WarriorFactory(current_health=-11, max_health=20)

    result = Warrior.objects.put_out_of_the_fight(obj=warrior, condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS)

    assert result.current_health == 0
    assert result.condition == Warrior.ConditionChoices.CONDITION_UNCONSCIOUS


@pytest.mark.django_db
def test_put_out_of_the_fight_leaves_a_warrior_dropped_exactly_to_nothing_alone():
    warrior = WarriorFactory(current_health=0, max_health=20)

    result = Warrior.objects.put_out_of_the_fight(obj=warrior, condition=Warrior.ConditionChoices.CONDITION_DEAD)

    assert result.current_health == 0


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
def test_replenish_current_morale_rallies_a_fleeing_warrior():
    """
    A rout with no wound in it is a normal way for a fight to end, and this is the only method that
    can clear it - the healing sweep never sees a warrior who is already at full health.
    """
    warrior = WarriorFactory(current_morale=0, max_morale=20, condition=Warrior.ConditionChoices.CONDITION_FLEEING)

    result = Warrior.objects.replenish_current_morale(obj=warrior, recovered_morale_points=20)

    assert result.current_morale == 20
    assert result.condition == Warrior.ConditionChoices.CONDITION_HEALTHY


@pytest.mark.django_db
def test_replenish_current_morale_rallies_a_fleeing_warrior_despite_his_wounds():
    """
    The rally does not wait on the health path: his nerve and his wounds are mended separately, and
    a man who has both is not left running until the second one is done.
    """
    warrior = WarriorFactory(
        current_morale=0,
        max_morale=20,
        current_health=5,
        max_health=20,
        condition=Warrior.ConditionChoices.CONDITION_FLEEING,
    )

    result = Warrior.objects.replenish_current_morale(obj=warrior, recovered_morale_points=20)

    assert result.current_health == 5
    assert result.condition == Warrior.ConditionChoices.CONDITION_HEALTHY


@pytest.mark.django_db
def test_replenish_current_morale_leaves_an_unconscious_warrior_unconscious():
    """
    The morale sweep excludes only the dead, so an unconscious warrior below his maximum reaches
    this method every month. Waking him here would take the healing sweep's decision away from it.
    """
    warrior = WarriorFactory(
        current_morale=0,
        max_morale=20,
        current_health=-5,
        max_health=20,
        condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS,
    )

    result = Warrior.objects.replenish_current_morale(obj=warrior, recovered_morale_points=20)

    assert result.current_morale == 20
    assert result.condition == Warrior.ConditionChoices.CONDITION_UNCONSCIOUS


@pytest.mark.django_db
def test_replenish_current_morale_leaves_a_dead_warrior_dead():
    warrior = WarriorFactory(current_morale=0, max_morale=20, condition=Warrior.ConditionChoices.CONDITION_DEAD)

    result = Warrior.objects.replenish_current_morale(obj=warrior, recovered_morale_points=20)

    assert result.condition == Warrior.ConditionChoices.CONDITION_DEAD


@pytest.mark.django_db
def test_replenish_current_morale_does_not_rally_a_warrior_whose_morale_is_still_zero():
    """
    Rallied to nothing is not rallied - a man handed back zero morale would rout again on the first
    blow of the next fight.
    """
    warrior = WarriorFactory(current_morale=0, max_morale=0, condition=Warrior.ConditionChoices.CONDITION_FLEEING)

    result = Warrior.objects.replenish_current_morale(obj=warrior, recovered_morale_points=0)

    assert result.current_morale == 0
    assert result.condition == Warrior.ConditionChoices.CONDITION_FLEEING


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


@pytest.mark.django_db
def test_get_payroll_for_faction_hands_over_the_cheapest_warrior_first():
    """
    The order is the rule: paying from the cheapest up fits the most men into whatever silver there
    is, and leaves the shortfall sitting on the veterans.
    """
    faction = FactionFactory()
    ealdorman = WarriorFactory(faction=faction, monthly_salary=300)
    levy = WarriorFactory(faction=faction, monthly_salary=50)
    thegn = WarriorFactory(faction=faction, monthly_salary=200)

    result = Warrior.objects.get_payroll_for_faction(faction=faction)

    assert result == [levy, thegn, ealdorman]


@pytest.mark.django_db
def test_get_payroll_for_faction_leaves_out_the_dead():
    faction = FactionFactory()
    survivor = WarriorFactory(faction=faction, monthly_salary=50)
    WarriorFactory(faction=faction, monthly_salary=50, condition=Warrior.ConditionChoices.CONDITION_DEAD)

    result = Warrior.objects.get_payroll_for_faction(faction=faction)

    assert result == [survivor]


@pytest.mark.django_db
def test_get_payroll_for_faction_leaves_out_another_factions_warriors():
    faction = FactionFactory()
    own_warrior = WarriorFactory(faction=faction, monthly_salary=50)
    WarriorFactory(monthly_salary=50)

    result = Warrior.objects.get_payroll_for_faction(faction=faction)

    assert result == [own_warrior]


@pytest.mark.django_db
def test_record_salaries_paid_forgives_the_months_they_went_without():
    first_warrior = WarriorFactory(unpaid_months=2)
    second_warrior = WarriorFactory(unpaid_months=1)

    Warrior.objects.record_salaries_paid(warrior_list=[first_warrior, second_warrior])

    first_warrior.refresh_from_db()
    second_warrior.refresh_from_db()
    assert (first_warrior.unpaid_months, second_warrior.unpaid_months) == (0, 0)


@pytest.mark.django_db
def test_record_salaries_unpaid_counts_another_month():
    first_warrior = WarriorFactory(unpaid_months=1)
    second_warrior = WarriorFactory(unpaid_months=0)

    Warrior.objects.record_salaries_unpaid(warrior_list=[first_warrior, second_warrior])

    first_warrior.refresh_from_db()
    second_warrior.refresh_from_db()
    assert (first_warrior.unpaid_months, second_warrior.unpaid_months) == (2, 1)


@pytest.mark.django_db
def test_record_salaries_unpaid_leaves_the_instances_carrying_the_new_count():
    """
    The unpaid warriors go straight onto an event, and the handler at the other end decides whether
    a man deserts by reading this count off them - so the objects have to be right, not just the rows.
    """
    warrior = WarriorFactory(unpaid_months=2)

    result = Warrior.objects.record_salaries_unpaid(warrior_list=[warrior])

    assert result[0].unpaid_months == 3


@pytest.mark.django_db
def test_strip_equipment_takes_back_weapon_and_armor():
    """
    An item belongs to the faction and is only wielded by a warrior, so gear left on a man who has
    walked off the roster is out of everyone's reach rather than in his hands.
    """
    weapon = ItemFactory(type=ItemTypeFactory(function=ItemType.FunctionChoices.FUNCTION_WEAPON))
    armor = ItemFactory(type=ItemTypeFactory(function=ItemType.FunctionChoices.FUNCTION_ARMOR))
    warrior = WarriorFactory(weapon=weapon, armor=armor)

    Warrior.objects.strip_equipment(obj=warrior)

    warrior.refresh_from_db()
    assert (warrior.weapon, warrior.armor) == (None, None)


@pytest.mark.django_db
def test_strip_equipment_leaves_the_owning_faction_alone():
    """
    Taking the gear back is what keeps it sellable - the faction has to still own it afterwards, or
    a deserter has robbed the war band on his way out.
    """
    faction = FactionFactory()
    weapon = ItemFactory(type=ItemTypeFactory(function=ItemType.FunctionChoices.FUNCTION_WEAPON), owner=faction)
    warrior = WarriorFactory(faction=faction, weapon=weapon)

    Warrior.objects.strip_equipment(obj=warrior)

    weapon.refresh_from_db()
    assert weapon.owner == faction


@pytest.mark.django_db
def test_transfer_equipment_ownership_hands_both_items_to_the_new_owner():
    faction = FactionFactory()
    weapon = ItemFactory(type=ItemTypeFactory(function=ItemType.FunctionChoices.FUNCTION_WEAPON))
    armor = ItemFactory(type=ItemTypeFactory(function=ItemType.FunctionChoices.FUNCTION_ARMOR))
    warrior = WarriorFactory(weapon=weapon, armor=armor)

    Warrior.objects.transfer_equipment_ownership(obj=warrior, new_owner=faction)

    weapon.refresh_from_db()
    armor.refresh_from_db()
    assert (weapon.owner, armor.owner) == (faction, faction)


@pytest.mark.django_db
def test_transfer_equipment_ownership_leaves_the_gear_on_the_warrior():
    """
    Unlike "Item.objects.update_ownership", which takes an item off its bearer as it changes hands -
    that would disarm the man the faction has just paid for.
    """
    faction = FactionFactory()
    weapon = ItemFactory(type=ItemTypeFactory(function=ItemType.FunctionChoices.FUNCTION_WEAPON))
    warrior = WarriorFactory(weapon=weapon)

    Warrior.objects.transfer_equipment_ownership(obj=warrior, new_owner=faction)

    warrior.refresh_from_db()
    assert warrior.weapon == weapon


@pytest.mark.django_db
def test_transfer_equipment_ownership_of_a_warrior_carrying_nothing():
    faction = FactionFactory()
    warrior = WarriorFactory(weapon=None, armor=None)

    result = Warrior.objects.transfer_equipment_ownership(obj=warrior, new_owner=faction)

    assert result == []
