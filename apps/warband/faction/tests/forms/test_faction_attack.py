import pytest

from apps.warband.faction.forms.faction_attack import FactionAttackForm
from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.quest.tests.factories.quest_contract import QuestContractFactory
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.warrior.services.availability import REASON_SWORN_TO_A_QUEST


@pytest.mark.django_db
def test_assignable_warriors_exclude_the_leader():
    """
    He is added in "get_assigned_warriors()" instead of being offered as a box the player could
    clear - the story has him joining every attack. Left out of the list entirely rather than greyed
    with a reason, because he is not unavailable, he is simply not a choice.
    """
    faction = FactionFactory()
    leader = WarriorFactory(faction=faction)
    follower = WarriorFactory(faction=faction)

    form = FactionAttackForm(leader=leader, month=3)

    assert list(form.fields["assigned_warriors"].queryset) == [follower]


@pytest.mark.django_db
def test_assignable_warriors_offer_a_warrior_on_a_quest_with_his_reason():
    """
    Drawn now rather than dropped. A picker holding three of five men said nothing about the other
    two, on this form as on the quest one.
    """
    faction = FactionFactory()
    leader = WarriorFactory(faction=faction)
    sworn_warrior = WarriorFactory(faction=faction)
    quest_contract = QuestContractFactory(faction=faction, accepted_in_month=3)
    quest_contract.assigned_warriors.add(sworn_warrior)

    form = FactionAttackForm(leader=leader, month=3)

    assert list(form.fields["assigned_warriors"].queryset) == [sworn_warrior]
    assert form.roster.reasons_by_warrior_id == {sworn_warrior.id: REASON_SWORN_TO_A_QUEST}


@pytest.mark.django_db
def test_assignable_warriors_exclude_another_factions_warrior():
    """
    The field holds the whole war band now so the page can draw the men who cannot march. The
    scoping it still performs is the faction one, or a hand-edited value marches a rival's warrior
    out under the player's banner.
    """
    faction = FactionFactory()
    leader = WarriorFactory(faction=faction)
    WarriorFactory(faction=FactionFactory(savegame=faction.savegame))

    form = FactionAttackForm(leader=leader, month=3)

    assert list(form.fields["assigned_warriors"].queryset) == []


@pytest.mark.django_db
def test_assignable_warriors_leave_out_a_dead_man():
    """
    The picker is measured against the roster the player reads on his faction page, and that one has
    no dead men on it either.
    """
    faction = FactionFactory()
    leader = WarriorFactory(faction=faction)
    WarriorFactory(faction=faction, condition=Warrior.ConditionChoices.CONDITION_DEAD)
    living_warrior = WarriorFactory(faction=faction)

    form = FactionAttackForm(leader=leader, month=3)

    assert list(form.fields["assigned_warriors"].queryset) == [living_warrior]


@pytest.mark.django_db
def test_empty_help_text_stays_away_while_there_are_rows_to_draw():
    """
    A roster of men who cannot march is not an empty picker: every one of them carries his own
    reason now, which is what the two deleted sentences used to approximate from a distance.
    """
    faction = FactionFactory()
    leader = WarriorFactory(faction=faction)
    WarriorFactory(faction=faction, condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS)

    form = FactionAttackForm(leader=leader, month=3)

    assert form.fields["assigned_warriors"].help_text == ""


@pytest.mark.django_db
def test_empty_help_text_names_a_roster_of_one():
    """
    The one state that draws no rows at all, and so the one the field still has to put into words.
    """
    faction = FactionFactory()
    leader = WarriorFactory(faction=faction)

    form = FactionAttackForm(leader=leader, month=3)

    assert form.fields["assigned_warriors"].help_text == (
        f"{FactionAttackForm.EMPTY_NO_OTHERS} {FactionAttackForm.EMPTY_TAIL}"
    )


@pytest.mark.django_db
def test_clean_assigned_warriors_refuses_a_man_who_cannot_march():
    """
    "disabled" keeps the browser from submitting the box and does nothing about a hand-edited post,
    and the queryset cannot be the gate any more - it has to hold him so the page can draw him.
    """
    faction = FactionFactory()
    leader = WarriorFactory(faction=faction)
    unfit_warrior = WarriorFactory(
        faction=faction, name="Beorn", condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS
    )

    form = FactionAttackForm(data={"assigned_warriors": [unfit_warrior.id]}, leader=leader, month=3)

    assert form.is_valid() is False
    assert form.errors["assigned_warriors"] == ["Beorn cannot march this month."]


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
