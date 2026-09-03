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
        attacker=WarriorFactory(faction=skirmish.attacking_faction),
        attacker_action=SkirmishActionChoices.SIMPLE_ATTACK,
        defender=WarriorFactory(faction=skirmish.defending_faction),
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


def test_deal_damage_floors_a_blow_the_defence_outmatches(damage_service):
    result = damage_service._deal_damage(attack=12, defense=20)

    assert result == 3
    assert damage_service.message_list == [
        WarriorTookDamage(
            skirmish=damage_service.skirmish,
            attacker=damage_service.attacker,
            attacker_damage=12,
            defender=damage_service.defender,
            defender_damage=20,
            # A quarter of the blow, because armour outmatching a weapon blunts it rather than
            # stopping it dead
            damage=3,
        )
    ]


def test_deal_damage_announces_a_fully_defended_attack(damage_service):
    """
    The floor is a share of the blow, so it rounds away on the smallest ones and the smallest blows
    can still be stopped dead. Two is the largest attack that behaves this way.
    """
    result = damage_service._deal_damage(attack=2, defense=7)

    assert result == 0
    assert damage_service.message_list == [
        WarriorDefendedAllDamage(
            skirmish=damage_service.skirmish,
            attacker=damage_service.attacker,
            defender=damage_service.defender,
            attacker_damage=2,
            defender_damage=7,
            # Passed on because whether the defender was turtling decides what the block does to his
            # nerve, and only the service knows which action he picked
            defender_action=damage_service.defender_action,
        )
    ]


def test_deal_damage_announces_an_attack_that_was_never_thrown(damage_service):
    result = damage_service._deal_damage(attack=0, defense=5)

    assert result == 0
    assert damage_service.message_list == [
        WarriorDefendedAllDamage(
            skirmish=damage_service.skirmish,
            attacker=damage_service.attacker,
            defender=damage_service.defender,
            attacker_damage=0,
            defender_damage=5,
            defender_action=damage_service.defender_action,
        )
    ]
