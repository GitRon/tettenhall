import pytest

from apps.warband.item.models.item_type import ItemType
from apps.warband.item.tests.factories.item import ItemFactory
from apps.warband.skirmish.choices.skirmish_action import SkirmishActionChoices
from apps.warband.skirmish.services.actions.requirements import (
    ACTION_REQUIREMENTS,
    ALWAYS_OFFERED,
    ActionRequirement,
    get_offered_actions,
)
from apps.warband.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory


def test_is_met_by_a_man_below_the_level():
    warrior = WarriorFactory.build(experience=0)

    assert ActionRequirement(minimum_level=2).is_met_by(warrior=warrior) is False


def test_is_met_by_a_man_at_the_level():
    warrior = WarriorFactory.build(experience=100)

    assert ActionRequirement(minimum_level=2).is_met_by(warrior=warrior) is True


@pytest.mark.django_db
def test_is_met_by_a_man_holding_the_weapon_it_names():
    weapon = ItemFactory(type=ItemType.objects.get(name="Spear"))
    warrior = WarriorFactory(weapon=weapon)

    assert ActionRequirement(weapon_types=frozenset({"Spear"})).is_met_by(warrior=warrior) is True


@pytest.mark.django_db
def test_is_met_by_a_man_holding_another_weapon():
    weapon = ItemFactory(type=ItemType.objects.get(name="Spear"))
    warrior = WarriorFactory(weapon=weapon)

    assert ActionRequirement(weapon_types=frozenset({"Unarmed"})).is_met_by(warrior=warrior) is False


@pytest.mark.django_db
def test_is_met_by_a_man_with_nothing_in_his_hands_reads_the_fallback():
    """
    Unarmed is an ordinary gear state, read the way the fight reads it, so the fallback row can carry
    an action list of its own.
    """
    warrior = WarriorFactory(weapon=None)

    assert ActionRequirement(weapon_types=frozenset({"Unarmed"})).is_met_by(warrior=warrior) is True


def test_always_offered_actions_carry_no_requirement():
    """
    The two a man must always have are kept out of the table, so no entry there can take them away.
    """
    assert {SkirmishActionChoices.SIMPLE_ATTACK, SkirmishActionChoices.FLEE} == ALWAYS_OFFERED
    assert ALWAYS_OFFERED.isdisjoint(ACTION_REQUIREMENTS)


@pytest.mark.parametrize(
    ("experience", "gained_action"),
    [
        (100, SkirmishActionChoices.DEFENSIVE_STANCE),
        (400, SkirmishActionChoices.FAST_ATTACK),
        (900, SkirmishActionChoices.RISKY_ATTACK),
    ],
)
@pytest.mark.django_db
def test_get_offered_actions_adds_one_action_at_each_threshold(experience, gained_action):
    skirmish = SkirmishFactory()
    below = WarriorFactory(faction=skirmish.attacking_faction, experience=experience - 1)
    at = WarriorFactory(faction=skirmish.attacking_faction, experience=experience)
    skirmish.attacking_warriors.add(below, at)

    offered_below = {action for action, _label in get_offered_actions(warrior=below, skirmish=skirmish)}
    offered_at = {action for action, _label in get_offered_actions(warrior=at, skirmish=skirmish)}

    assert offered_at - offered_below == {gained_action}
