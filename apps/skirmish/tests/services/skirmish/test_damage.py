from unittest import mock

import pytest

from apps.common.domain.dice import DiceNotation, DiceRoll
from apps.item.models.item_type import ItemType
from apps.item.tests.factories.item import ItemFactory
from apps.item.tests.factories.item_type import ItemTypeFactory
from apps.skirmish.choices.blow_outcome import BlowOutcomeChoices
from apps.skirmish.choices.skirmish_action import SkirmishActionChoices
from apps.skirmish.domain.action_roll import ActionRoll
from apps.skirmish.messages.events.warrior import WarriorDefendedAllDamage, WarriorTookDamage
from apps.skirmish.services.skirmish.damage import SkirmishDamageService
from apps.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.skirmish.tests.factories.warrior import WarriorFactory


def _attack_of(value: int) -> ActionRoll:
    return ActionRoll(roll=DiceRoll(notation=DiceNotation(dice_string="2d6"), result=value), value=value)


def _defense_of(value: int) -> ActionRoll:
    return ActionRoll(roll=DiceRoll(notation=DiceNotation(dice_string="4d6"), result=value), value=value)


@pytest.fixture
def damage_service(db) -> SkirmishDamageService:
    skirmish = SkirmishFactory()

    return SkirmishDamageService(
        skirmish=skirmish,
        round_number=3,
        attacker=WarriorFactory(faction=skirmish.attacking_faction),
        attacker_action=SkirmishActionChoices.SIMPLE_ATTACK,
        defender=WarriorFactory(faction=skirmish.defending_faction),
        defender_action=SkirmishActionChoices.SIMPLE_ATTACK,
    )


def test_deal_damage_announces_the_damage_getting_through(damage_service):
    attack = _attack_of(7)
    defense = _defense_of(2)

    result = damage_service._deal_damage(attack=attack, defense=defense)

    assert result == 5
    assert damage_service.message_list == [
        WarriorTookDamage(
            skirmish=damage_service.skirmish,
            round_number=3,
            attacker=damage_service.attacker,
            attacker_action=damage_service.attack_action,
            attack=attack,
            defender=damage_service.defender,
            defender_action=damage_service.defender_action,
            defense=defense,
            damage=5,
        )
    ]


def test_deal_damage_floors_a_blow_the_defence_outmatches(damage_service):
    attack = _attack_of(12)
    defense = _defense_of(20)

    result = damage_service._deal_damage(attack=attack, defense=defense)

    assert result == 3
    assert damage_service.message_list == [
        WarriorTookDamage(
            skirmish=damage_service.skirmish,
            round_number=3,
            attacker=damage_service.attacker,
            attacker_action=damage_service.attack_action,
            attack=attack,
            defender=damage_service.defender,
            defender_action=damage_service.defender_action,
            defense=defense,
            # A quarter of the blow, because armour outmatching a weapon blunts it rather than
            # stopping it dead
            damage=3,
        )
    ]


def test_deal_damage_announces_a_fully_defended_attack(damage_service):
    """
    The floor is a share of the blow rounded to whole points, so it rounds away on the smallest ones
    and those can still be stopped dead. Two is the largest attack that behaves this way, because
    round() takes a half to the even side and so takes this one down.
    """
    attack = _attack_of(2)
    defense = _defense_of(7)

    result = damage_service._deal_damage(attack=attack, defense=defense)

    assert result == 0
    assert damage_service.message_list == [
        WarriorDefendedAllDamage(
            skirmish=damage_service.skirmish,
            round_number=3,
            attacker=damage_service.attacker,
            attacker_action=damage_service.attack_action,
            attack=attack,
            defender=damage_service.defender,
            # Passed on because whether the defender was turtling decides what the block does to his
            # nerve, and only the service knows which action he picked
            defender_action=damage_service.defender_action,
            defense=defense,
            outcome=BlowOutcomeChoices.OUTCOME_ABSORBED,
        )
    ]


def test_deal_damage_announces_an_attack_that_was_never_thrown(damage_service):
    """
    An action that declined to swing keeps its own name for it rather than being read as armour that
    held - the two are the same zero and are not the same event.
    """
    attack = ActionRoll(roll=None, value=0, outcome=BlowOutcomeChoices.OUTCOME_NOT_THROWN)
    defense = _defense_of(5)

    result = damage_service._deal_damage(attack=attack, defense=defense)

    assert result == 0
    assert damage_service.message_list == [
        WarriorDefendedAllDamage(
            skirmish=damage_service.skirmish,
            round_number=3,
            attacker=damage_service.attacker,
            attacker_action=damage_service.attack_action,
            attack=attack,
            defender=damage_service.defender,
            defender_action=damage_service.defender_action,
            defense=defense,
            outcome=BlowOutcomeChoices.OUTCOME_NOT_THROWN,
        )
    ]


@pytest.mark.django_db
def test_process_sets_each_mans_own_gear_and_action_against_the_others():
    """
    The composition, not the arithmetic: each side's service is built from that side's action and that
    side's warrior, and the two rolls reach "_deal_damage" the right way round.

    Distinct dice per man is what makes this test able to fail. With both of them on the fallback the
    two sides swap to the same numbers, and every other test here hands "_deal_damage" its rolls
    ready-made - so a crossed pair would be recorded as the wrong man's die and nothing would notice.
    """
    skirmish = SkirmishFactory()
    savegame = skirmish.attacking_faction.savegame
    attacker = WarriorFactory(
        faction=skirmish.attacking_faction,
        weapon=ItemFactory(
            savegame=savegame,
            type=ItemTypeFactory(base_value="2d6", function=ItemType.FunctionChoices.FUNCTION_WEAPON),
        ),
    )
    defender = WarriorFactory(
        faction=skirmish.defending_faction,
        armor=ItemFactory(
            savegame=savegame,
            type=ItemTypeFactory(base_value="1d4", function=ItemType.FunctionChoices.FUNCTION_ARMOR),
        ),
    )
    service = SkirmishDamageService(
        skirmish=skirmish,
        round_number=2,
        attacker=attacker,
        attacker_action=SkirmishActionChoices.SIMPLE_ATTACK,
        defender=defender,
        defender_action=SkirmishActionChoices.DEFENSIVE_STANCE,
    )

    # Patched at the boundary: the die behind both rolls
    with mock.patch("apps.common.domain.dice.random.randint", return_value=3):
        result = service.process()

    assert result == [
        WarriorTookDamage(
            skirmish=skirmish,
            round_number=2,
            attacker=attacker,
            attacker_action=SkirmishActionChoices.SIMPLE_ATTACK,
            attack=ActionRoll(roll=DiceRoll(notation=DiceNotation(dice_string="2d6"), result=6), value=6),
            defender=defender,
            defender_action=SkirmishActionChoices.DEFENSIVE_STANCE,
            # The stance doubles the value and leaves the die it doubled from as it fell
            defense=ActionRoll(roll=DiceRoll(notation=DiceNotation(dice_string="1d4"), result=3), value=6),
            damage=2,
        )
    ]
