import pytest

from apps.faction.forms.faction_attack import FactionAttackForm
from apps.faction.tests.factories.faction import FactionFactory
from apps.quest.tests.factories.quest_contract import QuestContractFactory
from apps.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_assignable_warriors_exclude_the_leader():
    """
    He is added in "get_assigned_warriors()" instead of being offered as a box the player could
    clear - the story has him joining every attack.
    """
    faction = FactionFactory()
    leader = WarriorFactory(faction=faction)
    follower = WarriorFactory(faction=faction)

    form = FactionAttackForm(leader=leader, month=3)

    assert list(form.fields["assigned_warriors"].queryset) == [follower]


@pytest.mark.django_db
def test_assignable_warriors_exclude_a_warrior_on_a_quest():
    faction = FactionFactory()
    leader = WarriorFactory(faction=faction)
    quest_contract = QuestContractFactory(faction=faction, accepted_in_month=3)
    quest_contract.assigned_warriors.add(WarriorFactory(faction=faction))

    form = FactionAttackForm(leader=leader, month=3)

    assert list(form.fields["assigned_warriors"].queryset) == []


@pytest.mark.django_db
def test_assignable_warriors_exclude_another_factions_warrior():
    """
    The field is what validates the posted ids, so left unscoped a hand-edited value would march a
    rival's warrior out under the player's banner.
    """
    faction = FactionFactory()
    leader = WarriorFactory(faction=faction)
    WarriorFactory(faction=FactionFactory(savegame=faction.savegame))

    form = FactionAttackForm(leader=leader, month=3)

    assert list(form.fields["assigned_warriors"].queryset) == []


@pytest.mark.django_db
def test_get_assigned_warriors_always_includes_the_leader():
    faction = FactionFactory()
    leader = WarriorFactory(faction=faction)
    follower = WarriorFactory(faction=faction)

    form = FactionAttackForm(data={"assigned_warriors": [follower.id]}, leader=leader, month=3)

    assert form.is_valid() is True
    assert form.get_assigned_warriors() == [leader, follower]


@pytest.mark.django_db
def test_get_assigned_warriors_marches_the_leader_out_alone():
    """
    A war band of one is a bad idea, not an invalid one, so the field is optional and the leader
    still turns up in the result.
    """
    faction = FactionFactory()
    leader = WarriorFactory(faction=faction)

    form = FactionAttackForm(data={}, leader=leader, month=3)

    assert form.is_valid() is True
    assert form.get_assigned_warriors() == [leader]
