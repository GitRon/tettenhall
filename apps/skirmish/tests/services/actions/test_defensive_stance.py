from unittest import mock

import pytest

from apps.skirmish.messages.events.warrior import WarriorDefendedDamage
from apps.skirmish.services.actions.defensive_stance import DefensiveStanceService
from apps.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.skirmish.tests.factories.warrior import WarriorFactory


def test_get_pair_matching_points_never_makes_the_warrior_the_attacker():
    result = DefensiveStanceService.get_pair_matching_points(warrior_dexterity=7)

    assert result == 0


@pytest.mark.django_db
def test_get_attack_value_never_deals_damage():
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.attacking_faction)
    service = DefensiveStanceService(skirmish=skirmish, warrior=warrior)

    result = service.get_attack_value()

    assert result == 0
    assert service.message_list == []


@pytest.mark.django_db
def test_get_defense_value_doubles_the_defense():
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.attacking_faction)
    service = DefensiveStanceService(skirmish=skirmish, warrior=warrior)

    # Patched at the boundary: the die behind "roll_defense()"
    with mock.patch("apps.common.domain.dice.random.randint", return_value=2):
        result = service.get_defense_value()

    assert result == 4
    # The undoubled roll is what the base service announces
    assert service.message_list == [WarriorDefendedDamage(skirmish=skirmish, warrior=warrior, damage=2)]
