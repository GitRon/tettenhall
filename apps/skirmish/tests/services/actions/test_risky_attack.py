from unittest import mock

import pytest

from apps.skirmish.messages.events.warrior import WarriorAttackedWithDamage
from apps.skirmish.services.actions.risky_attack import RiskyAttackService
from apps.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_get_attack_value_doubles_the_damage_on_a_hit():
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.attacking_faction, strength=10)
    service = RiskyAttackService(skirmish=skirmish, warrior=warrior)

    # Patched at the boundary: the coin flip deciding hit or miss, and the die behind "roll_attack()"
    with (
        mock.patch("apps.skirmish.services.actions.risky_attack.random.getrandbits", return_value=1),
        mock.patch("apps.common.domain.dice.random.randint", return_value=3),
    ):
        result = service.get_attack_value()

    assert result == 6
    assert service.message_list == [WarriorAttackedWithDamage(skirmish=skirmish, warrior=warrior, damage=6)]


@pytest.mark.django_db
def test_get_attack_value_deals_nothing_on_a_miss():
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.attacking_faction, strength=10)
    service = RiskyAttackService(skirmish=skirmish, warrior=warrior)

    with mock.patch("apps.skirmish.services.actions.risky_attack.random.getrandbits", return_value=0):
        result = service.get_attack_value()

    assert result == 0
    assert service.message_list == [WarriorAttackedWithDamage(skirmish=skirmish, warrior=warrior, damage=0)]
