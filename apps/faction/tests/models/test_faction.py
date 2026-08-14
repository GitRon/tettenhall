import pytest

from apps.faction.tests.factories.faction import FactionFactory
from apps.quest.tests.factories.quest_contract import QuestContractFactory
from apps.skirmish.models.warrior import Warrior
from apps.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.skirmish.tests.factories.warrior import WarriorFactory


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
    skirmish = SkirmishFactory(player_faction=faction, victorious_faction=faction, month=3)
    skirmish.player_warriors.add(faction.leader)

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
