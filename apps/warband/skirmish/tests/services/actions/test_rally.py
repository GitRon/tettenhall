from unittest import mock

import pytest

from apps.warband.skirmish.choices.blow_outcome import BlowOutcomeChoices
from apps.warband.skirmish.domain.action_roll import ActionRoll
from apps.warband.skirmish.services.actions.base import AttackService
from apps.warband.skirmish.services.actions.rally import RallyService
from apps.warband.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory


def test_get_pair_matching_points_never_makes_the_leader_the_attacker():
    result = RallyService.get_pair_matching_points(warrior_dexterity=7)

    assert result == 0


@pytest.mark.django_db
def test_get_attack_value_throws_nothing():
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.attacking_faction)

    result = RallyService(skirmish=skirmish, warrior=warrior).get_attack_value()

    assert result == ActionRoll(roll=None, value=0, outcome=BlowOutcomeChoices.OUTCOME_NOT_THROWN)


@pytest.mark.django_db
def test_get_defense_value_is_his_plain_guard():
    """
    He gives up his swing and nothing else: neither weakened nor doubled like the stance.
    """
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.attacking_faction)

    with mock.patch("apps.common.domain.dice.random.randint", return_value=2):
        result = RallyService(skirmish=skirmish, warrior=warrior).get_defense_value()
    with mock.patch("apps.common.domain.dice.random.randint", return_value=2):
        plain = AttackService(skirmish=skirmish, warrior=warrior).get_defense_value()

    assert result == plain
