import pytest

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.quest.tests.factories.quest_contract import QuestContractFactory
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.warrior.services.availability import (
    REASON_COMMITTED_TO_A_FIGHT,
    REASON_STANDING_IN_AN_OPEN_FIGHT,
    REASON_SWORN_TO_A_QUEST,
    assess_roster,
)


@pytest.mark.django_db
def test_assess_roster_clears_a_man_nothing_is_holding():
    faction = FactionFactory()
    warrior = WarriorFactory(faction=faction, name="Eadric")

    result = assess_roster(faction_id=faction.id, month=3)

    assert result.assessed[0].warrior == warrior
    assert result.assessed[0].reason is None


@pytest.mark.django_db
def test_assess_roster_names_his_condition_for_a_man_who_cannot_fight():
    """
    Read off the field's own choices rather than worded a second time in the service.
    """
    faction = FactionFactory()
    WarriorFactory(faction=faction, condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS)

    result = assess_roster(faction_id=faction.id, month=3)

    assert result.assessed[0].reason == "Unconscious"


@pytest.mark.django_db
def test_assess_roster_names_the_quest_a_man_is_already_sworn_to():
    faction = FactionFactory()
    warrior = WarriorFactory(faction=faction)
    quest_contract = QuestContractFactory(faction=faction, accepted_in_month=3)
    quest_contract.assigned_warriors.add(warrior)

    result = assess_roster(faction_id=faction.id, month=3)

    assert result.assessed[0].reason == REASON_SWORN_TO_A_QUEST


@pytest.mark.django_db
def test_assess_roster_names_the_fight_a_man_is_committed_to_this_month():
    faction = FactionFactory()
    warrior = WarriorFactory(faction=faction)
    skirmish = SkirmishFactory(attacking_faction=faction, month=3, victorious_faction=None)
    skirmish.attacking_warriors.add(warrior)

    result = assess_roster(faction_id=faction.id, month=3)

    assert result.assessed[0].reason == REASON_COMMITTED_TO_A_FIGHT


@pytest.mark.django_db
def test_assess_roster_names_the_open_fight_of_another_month():
    """
    The exclusion the issue behind this was written for. A fight the player walked away from keeps
    everyone on either roster out of everything, in a month whose own skirmish list is empty.
    """
    faction = FactionFactory()
    warrior = WarriorFactory(faction=faction)
    skirmish = SkirmishFactory(attacking_faction=faction, month=1, victorious_faction=None)
    skirmish.attacking_warriors.add(warrior)

    result = assess_roster(faction_id=faction.id, month=3)

    assert result.assessed[0].reason == REASON_STANDING_IN_AN_OPEN_FIGHT


@pytest.mark.django_db
def test_assess_roster_names_only_the_first_rule_that_catches_a_man():
    """
    A dead man on a quest roster is dead before he is spoken for.
    """
    faction = FactionFactory()
    warrior = WarriorFactory(faction=faction, condition=Warrior.ConditionChoices.CONDITION_DEAD)
    quest_contract = QuestContractFactory(faction=faction, accepted_in_month=3)
    quest_contract.assigned_warriors.add(warrior)

    result = assess_roster(faction_id=faction.id, month=3)

    assert result.assessed[0].reason == "Dead"


@pytest.mark.django_db
def test_assess_roster_leaves_out_a_man_the_caller_excluded():
    """
    The attack form's leader, who marches whatever the player ticks. Left out entirely rather than
    greyed with a reason - "he is coming regardless" is not a reason he cannot go.
    """
    faction = FactionFactory()
    leader = WarriorFactory(faction=faction)
    follower = WarriorFactory(faction=faction)

    result = assess_roster(faction_id=faction.id, month=3, excluded_ids=(leader.id,))

    assert [assessment.warrior for assessment in result.assessed] == [follower]


@pytest.mark.django_db
def test_assess_roster_leaves_out_another_factions_warrior():
    faction = FactionFactory()
    WarriorFactory(faction=FactionFactory(savegame=faction.savegame))

    result = assess_roster(faction_id=faction.id, month=3)

    assert result.assessed == ()


@pytest.mark.django_db
def test_assess_roster_orders_by_name_rather_than_by_availability():
    """
    Sorting the unavailable to the bottom would undo the one thing drawing them achieves, which is
    that the list reads as the war band the player owns.
    """
    faction = FactionFactory()
    WarriorFactory(faction=faction, name="Beorn", condition=Warrior.ConditionChoices.CONDITION_DEAD)
    WarriorFactory(faction=faction, name="Cynric")

    result = assess_roster(faction_id=faction.id, month=3)

    assert [assessment.warrior.name for assessment in result.assessed] == ["Beorn", "Cynric"]


@pytest.mark.django_db
def test_is_empty_of_a_faction_with_nobody_on_the_roster():
    faction = FactionFactory()

    result = assess_roster(faction_id=faction.id, month=3)

    assert result.is_empty is True


@pytest.mark.django_db
def test_is_empty_of_a_roster_nobody_on_which_can_go():
    """
    A page full of greyed rows is not an empty page, and the two say different things.
    """
    faction = FactionFactory()
    WarriorFactory(faction=faction, condition=Warrior.ConditionChoices.CONDITION_DEAD)

    result = assess_roster(faction_id=faction.id, month=3)

    assert result.is_empty is False


@pytest.mark.django_db
def test_has_nobody_available_when_every_man_is_spoken_for():
    faction = FactionFactory()
    WarriorFactory(faction=faction, condition=Warrior.ConditionChoices.CONDITION_DEAD)

    result = assess_roster(faction_id=faction.id, month=3)

    assert result.has_nobody_available is True


@pytest.mark.django_db
def test_has_nobody_available_when_one_man_can_still_go():
    faction = FactionFactory()
    WarriorFactory(faction=faction, condition=Warrior.ConditionChoices.CONDITION_DEAD)
    WarriorFactory(faction=faction)

    result = assess_roster(faction_id=faction.id, month=3)

    assert result.has_nobody_available is False


@pytest.mark.django_db
def test_reasons_by_warrior_id_carries_only_the_men_who_cannot_go():
    faction = FactionFactory()
    unfit_warrior = WarriorFactory(faction=faction, condition=Warrior.ConditionChoices.CONDITION_FLEEING)
    WarriorFactory(faction=faction)

    result = assess_roster(faction_id=faction.id, month=3)

    assert result.reasons_by_warrior_id == {unfit_warrior.id: "Fleeing"}


@pytest.mark.django_db
def test_available_ids_carries_only_the_men_who_can():
    faction = FactionFactory()
    WarriorFactory(faction=faction, condition=Warrior.ConditionChoices.CONDITION_FLEEING)
    able_warrior = WarriorFactory(faction=faction)

    result = assess_roster(faction_id=faction.id, month=3)

    assert result.available_ids == {able_warrior.id}


@pytest.mark.django_db
def test_as_queryset_holds_the_unavailable_men_too():
    """
    An option missing from the field's queryset is an option that does not render, and drawing the
    men who cannot go is the whole point.
    """
    faction = FactionFactory()
    unfit_warrior = WarriorFactory(faction=faction, name="Beorn", condition=Warrior.ConditionChoices.CONDITION_DEAD)
    able_warrior = WarriorFactory(faction=faction, name="Cynric")

    result = assess_roster(faction_id=faction.id, month=3)

    assert list(result.as_queryset()) == [unfit_warrior, able_warrior]
