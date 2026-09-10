import pytest

from apps.warband.faction.forms.faction_attack import FactionAttackForm
from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.quest.tests.factories.quest_contract import QuestContractFactory
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory


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
def test_empty_help_text_stays_away_while_somebody_can_march():
    faction = FactionFactory()
    leader = WarriorFactory(faction=faction)
    WarriorFactory(faction=faction)

    form = FactionAttackForm(leader=leader, month=3)

    assert form.fields["assigned_warriors"].help_text == ""


@pytest.mark.django_db
def test_empty_help_text_names_a_roster_of_one():
    faction = FactionFactory()
    leader = WarriorFactory(faction=faction)

    form = FactionAttackForm(leader=leader, month=3)

    assert form.fields["assigned_warriors"].help_text == (
        f"{FactionAttackForm.EMPTY_NO_OTHERS} {FactionAttackForm.EMPTY_TAIL}"
    )


@pytest.mark.django_db
def test_empty_help_text_names_the_wounded():
    """
    The state the entry was found in: one man unconscious, one dead, and a picker with no options in
    it that said nothing about either.
    """
    faction = FactionFactory()
    leader = WarriorFactory(faction=faction)
    WarriorFactory(faction=faction, condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS)
    WarriorFactory(faction=faction, condition=Warrior.ConditionChoices.CONDITION_DEAD)

    form = FactionAttackForm(leader=leader, month=3)

    assert form.fields["assigned_warriors"].help_text == (
        f"{FactionAttackForm.EMPTY_NONE_ABLE} {FactionAttackForm.EMPTY_TAIL}"
    )


@pytest.mark.django_db
def test_empty_help_text_names_the_committed():
    """
    Able to march and spoken for, which is the one of the three the player can still do something
    about - next month.
    """
    faction = FactionFactory()
    leader = WarriorFactory(faction=faction)
    quest_contract = QuestContractFactory(faction=faction, accepted_in_month=3)
    quest_contract.assigned_warriors.add(WarriorFactory(faction=faction))

    form = FactionAttackForm(leader=leader, month=3)

    assert form.fields["assigned_warriors"].help_text == (
        f"{FactionAttackForm.EMPTY_ALL_COMMITTED} {FactionAttackForm.EMPTY_TAIL}"
    )


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
