import pytest

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.quest.tests.factories.quest_contract import QuestContractFactory
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.warrior.tests.factories.injury import InjuryFactory


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
def test_get_held_captives_brings_the_injuries_along(django_assert_num_queries):
    """
    The card names every mark a prisoner carries, so a bare related manager would cost a query per
    man plus one per injury - see [get_all_living_warriors], which exists for the same reason.
    """
    faction = FactionFactory()
    captive = WarriorFactory(faction=None, savegame=faction.savegame, culture=faction.culture)
    faction.captured_warriors.add(captive)
    InjuryFactory(warrior=captive)

    held_captive = faction.get_held_captives().get()

    # The prefetch already has them, so reading the row and its catalogue entry costs nothing more
    with django_assert_num_queries(0):
        assert held_captive.injuries.all()[0].type.name


@pytest.mark.django_db
def test_get_pub_stock_is_the_men_on_the_shelf():
    faction = FactionFactory()
    mercenary = WarriorFactory(faction=None, savegame=faction.savegame, culture=faction.culture, is_pub_stock=True)
    faction.available_mercenaries.add(mercenary)
    WarriorFactory(faction=faction)

    assert list(faction.get_pub_stock()) == [mercenary]
