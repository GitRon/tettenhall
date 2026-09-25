import pytest

from apps.warband.skirmish.choices.skirmish_action import SkirmishActionChoices
from apps.warband.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.templatetags.skirmish_actions import decided_action, offered_actions


@pytest.mark.django_db
def test_offered_actions_asks_the_fight():
    skirmish = SkirmishFactory(fortification_strength=0)
    warrior = WarriorFactory(faction=skirmish.attacking_faction)
    skirmish.attacking_warriors.add(warrior)

    result = offered_actions(warrior, skirmish)

    assert (SkirmishActionChoices.ASSAULT_FORTIFICATION, "Assault the fortification") not in result


@pytest.mark.django_db
def test_decided_action_names_what_the_ai_orders():
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(
        faction=skirmish.defending_faction, current_health=20, max_health=20, dexterity=10, strength=10
    )

    result = decided_action(warrior, skirmish)

    assert result == SkirmishActionChoices.SIMPLE_ATTACK.label
