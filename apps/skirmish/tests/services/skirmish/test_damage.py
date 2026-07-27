import pytest

from apps.skirmish.choices.skirmish_action import SkirmishActionChoices
from apps.skirmish.messages.events.warrior import WarriorDefendedAllDamage, WarriorTookDamage
from apps.skirmish.services.skirmish.damage import SkirmishDamageService
from apps.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.skirmish.tests.factories.warrior import WarriorFactory


@pytest.fixture
def damage_service(db) -> SkirmishDamageService:
    skirmish = SkirmishFactory()

    return SkirmishDamageService(
        skirmish=skirmish,
        attacker=WarriorFactory(faction=skirmish.player_faction),
        attacker_action=SkirmishActionChoices.SIMPLE_ATTACK,
        defender=WarriorFactory(faction=skirmish.non_player_faction),
        defender_action=SkirmishActionChoices.SIMPLE_ATTACK,
    )


def test_deal_damage_announces_the_damage_getting_through(damage_service):
    result = damage_service._deal_damage(attack=7, defense=2)

    assert result == 5
    assert damage_service.message_list == [
        WarriorTookDamage(
            skirmish=damage_service.skirmish,
            attacker=damage_service.attacker,
            attacker_damage=7,
            defender=damage_service.defender,
            defender_damage=2,
            damage=5,
        )
    ]


def test_deal_damage_announces_a_fully_defended_attack(damage_service):
    result = damage_service._deal_damage(attack=2, defense=7)

    assert result == 0
    assert damage_service.message_list == [
        WarriorDefendedAllDamage(
            skirmish=damage_service.skirmish,
            attacker=damage_service.attacker,
            defender=damage_service.defender,
            attacker_damage=2,
            defender_damage=7,
        )
    ]
