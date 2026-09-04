from unittest import mock

import pytest

from apps.skirmish.messages.events.warrior import WarriorAttackedWithDamage
from apps.skirmish.services.actions.fast_attack import FastAttackService
from apps.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.skirmish.tests.factories.warrior import WarriorFactory


def test_get_pair_matching_points_doubles_the_base_points():
    result = FastAttackService.get_pair_matching_points(warrior_dexterity=7)

    assert result == 14


@pytest.mark.django_db
def test_get_attack_value_halves_the_damage():
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.attacking_faction, strength=20)
    service = FastAttackService(skirmish=skirmish, warrior=warrior)

    # Patched at the boundary: the die behind "roll_attack()"
    with mock.patch("apps.common.domain.dice.random.randint", return_value=3):
        result = service.get_attack_value()

    assert result == 3
    assert service.message_list == [WarriorAttackedWithDamage(skirmish=skirmish, warrior=warrior, damage=3)]


@pytest.mark.django_db
def test_get_attack_value_halves_a_blow_measured_against_a_lower_baseline():
    """
    The halving sits on top of the strength comparison rather than replacing it, so a levy swinging
    fast is measured against a levy's mean and not against a number this service holds.
    """
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.attacking_faction, strength=20, strength_baseline=5)
    service = FastAttackService(skirmish=skirmish, warrior=warrior)

    with mock.patch("apps.common.domain.dice.random.randint", return_value=3):
        result = service.get_attack_value()

    assert result == 6
    assert service.message_list == [WarriorAttackedWithDamage(skirmish=skirmish, warrior=warrior, damage=6)]
