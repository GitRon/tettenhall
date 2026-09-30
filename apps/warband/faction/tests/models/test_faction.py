import pytest

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.item.tests.factories.item import ItemFactory
from apps.warband.quest.tests.factories.quest_contract import QuestContractFactory
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.town.models import Town
from apps.warband.warrior.services.portrait import draw_portrait


@pytest.mark.django_db
def test_renown_is_the_leaders():
    faction = FactionFactory()
    faction.leader = WarriorFactory(faction=faction, renown=45)
    faction.save()

    assert faction.renown == 45


@pytest.mark.django_db
def test_renown_of_a_defeated_faction_is_nothing():
    """
    The leader relation outlives the defeat, so his renown would still be readable through it.
    """
    faction = FactionFactory(is_defeated=True)
    faction.leader = WarriorFactory(faction=faction, renown=45)
    faction.save()

    assert faction.renown == 0


@pytest.mark.django_db
def test_renown_without_a_leader():
    faction = FactionFactory(leader=None)

    assert faction.renown == 0


@pytest.mark.django_db
def test_get_available_leader_returns_the_leader():
    faction = FactionFactory()
    faction.leader = WarriorFactory(faction=faction)
    faction.save()

    result = faction.get_available_leader(month=3)

    assert result == faction.leader


@pytest.mark.django_db
def test_get_available_leader_without_a_leader():
    """
    Faction.leader is nullable, and a faction that has lost its leader has nobody to march behind.
    """
    faction = FactionFactory(leader=None)

    result = faction.get_available_leader(month=3)

    assert result is None


@pytest.mark.django_db
def test_get_available_leader_with_a_wounded_leader():
    faction = FactionFactory()
    faction.leader = WarriorFactory(faction=faction, condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS)
    faction.save()

    result = faction.get_available_leader(month=3)

    assert result is None


@pytest.mark.django_db
def test_has_marched_this_month_after_a_fight():
    faction = FactionFactory()
    faction.leader = WarriorFactory(faction=faction)
    faction.save()
    skirmish = SkirmishFactory(attacking_faction=faction, victorious_faction=faction, month=3)
    skirmish.attacking_warriors.add(faction.leader)

    result = faction.has_marched_this_month(month=3)

    assert result is True


@pytest.mark.django_db
def test_has_marched_this_month_with_an_idle_war_band():
    faction = FactionFactory()
    faction.leader = WarriorFactory(faction=faction)
    faction.save()

    result = faction.has_marched_this_month(month=3)

    assert result is False


@pytest.mark.django_db
def test_has_marched_this_month_without_a_leader():
    """
    Nobody to march, which is not the same as having marched - the player is told why the attack is
    gone only when the reason is that his warriors are already out.
    """
    faction = FactionFactory(leader=None)

    result = faction.has_marched_this_month(month=3)

    assert result is False


@pytest.mark.django_db
def test_get_available_leader_with_a_leader_on_a_quest():
    faction = FactionFactory()
    faction.leader = WarriorFactory(faction=faction)
    faction.save()
    quest_contract = QuestContractFactory(faction=faction, accepted_in_month=3)
    quest_contract.assigned_warriors.add(faction.leader)

    result = faction.get_available_leader(month=3)

    assert result is None


@pytest.mark.django_db
def test_get_all_living_warriors_is_the_faction_s_own_roster():
    faction = FactionFactory()
    warrior = WarriorFactory(faction=faction)
    WarriorFactory(faction=FactionFactory(savegame=faction.savegame))

    assert list(faction.get_all_living_warriors()) == [warrior]


@pytest.mark.django_db
def test_get_all_living_warriors_leaves_the_dead_out():
    faction = FactionFactory()
    WarriorFactory(faction=faction, condition=Warrior.ConditionChoices.CONDITION_DEAD)

    assert list(faction.get_all_living_warriors()) == []


@pytest.mark.django_db
def test_get_held_captives_is_the_men_in_the_cells():
    faction = FactionFactory()
    captive = WarriorFactory(faction=None, savegame=faction.savegame, culture=faction.culture)
    faction.captured_warriors.add(captive)
    WarriorFactory(faction=faction)

    assert list(faction.get_held_captives()) == [captive]


@pytest.mark.django_db
def test_get_held_captives_brings_the_gear_along(django_assert_num_queries):
    """
    The row names the weapon and the armour a prisoner carries, and an item's name reads its type, so
    a bare related manager would cost up to four queries per man.
    """
    faction = FactionFactory()
    captive = WarriorFactory(
        faction=None,
        savegame=faction.savegame,
        culture=faction.culture,
        weapon=ItemFactory(savegame=faction.savegame),
        armor=ItemFactory(savegame=faction.savegame),
    )
    faction.captured_warriors.add(captive)

    held_captive = faction.get_held_captives().get()

    with django_assert_num_queries(0):
        assert held_captive.weapon.display_name and held_captive.armor.display_name


@pytest.mark.django_db
def test_get_pub_stock_is_the_men_on_the_shelf():
    faction = FactionFactory()
    mercenary = WarriorFactory(faction=None, savegame=faction.savegame, culture=faction.culture, is_pub_stock=True)
    faction.available_mercenaries.add(mercenary)
    WarriorFactory(faction=faction)

    assert list(faction.get_pub_stock()) == [mercenary]


@pytest.mark.django_db
def test_get_pub_stock_brings_the_gear_along(django_assert_num_queries):
    """The twin of [test_get_held_captives_brings_the_gear_along], for the pub's rows."""
    faction = FactionFactory()
    mercenary = WarriorFactory(
        faction=None,
        savegame=faction.savegame,
        culture=faction.culture,
        is_pub_stock=True,
        weapon=ItemFactory(savegame=faction.savegame),
        armor=ItemFactory(savegame=faction.savegame),
    )
    faction.available_mercenaries.add(mercenary)

    stocked_mercenary = faction.get_pub_stock().get()

    with django_assert_num_queries(0):
        assert stocked_mercenary.weapon.display_name and stocked_mercenary.armor.display_name


@pytest.mark.django_db
def test_get_pub_stock_brings_the_savegame_along(django_assert_num_queries):
    """
    Every row prints a man's price, which reads how long he has waited off his savegame's month - a
    query per mercenary if the savegame does not come along.
    """
    faction = FactionFactory()
    mercenary = WarriorFactory(
        faction=None,
        savegame=faction.savegame,
        culture=faction.culture,
        is_pub_stock=True,
        pub_arrival_month=faction.savegame.current_month,
    )
    faction.available_mercenaries.add(mercenary)

    stocked_mercenary = faction.get_pub_stock().get()

    with django_assert_num_queries(0):
        assert stocked_mercenary.months_in_pub == 0


@pytest.mark.django_db
def test_get_monthly_income_counts_only_the_men_drawing_a_wage():
    """
    A leader draws nothing and the dead are paid nothing, so neither mans the hall: two of the four
    here count, which is a Great Hall paid in full.
    """
    faction = FactionFactory(town__hall=Town.HallChoices.HALL_MEDIUM)
    faction.leader = WarriorFactory(faction=faction, monthly_salary=0)
    faction.save()
    WarriorFactory.create_batch(2, faction=faction, monthly_salary=10)
    WarriorFactory(faction=faction, monthly_salary=10, condition=Warrior.ConditionChoices.CONDITION_DEAD)

    assert faction.get_monthly_income() == 550


@pytest.mark.django_db
def test_get_held_captives_brings_the_portrait_along(django_assert_num_queries):
    """Every row draws the prisoner's face, which is five foreign keys."""
    faction = FactionFactory()
    captive = WarriorFactory(faction=None, savegame=faction.savegame, culture=faction.culture, **draw_portrait())
    faction.captured_warriors.add(captive)

    held_captive = faction.get_held_captives().get()

    with django_assert_num_queries(0):
        assert held_captive.portrait_face.image and held_captive.hair_colour.hex


@pytest.mark.django_db
def test_get_pub_stock_brings_the_portrait_along(django_assert_num_queries):
    """The twin of [test_get_held_captives_brings_the_portrait_along], for the pub's rows."""
    faction = FactionFactory()
    mercenary = WarriorFactory(
        faction=None, savegame=faction.savegame, culture=faction.culture, is_pub_stock=True, **draw_portrait()
    )
    faction.available_mercenaries.add(mercenary)

    stocked_mercenary = faction.get_pub_stock().get()

    with django_assert_num_queries(0):
        assert stocked_mercenary.portrait_face.image and stocked_mercenary.hair_colour.hex
