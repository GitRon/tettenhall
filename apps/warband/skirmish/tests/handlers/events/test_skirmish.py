import pytest

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.skirmish.choices.initiative import InitiativeChoices
from apps.warband.skirmish.choices.skirmish_action import SkirmishActionChoices
from apps.warband.skirmish.handlers.events.skirmish import (
    handle_attacker_defender_decided,
    handle_create_skirmish_for_attack,
    handle_round_finished,
)
from apps.warband.skirmish.messages.commands.skirmish import CreateSkirmish, WarriorAttacksWarrior, WinSkirmish
from apps.warband.skirmish.messages.events.skirmish import AttackerDefenderDecided, FactionWasAttacked, RoundFinished
from apps.warband.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory


def test_handle_create_skirmish_for_attack_maps_to_the_command():
    attacking_faction = FactionFactory.build(name="Mercia")
    defending_faction = FactionFactory.build(name="Wessex")
    attacker = WarriorFactory.build(faction=attacking_faction)
    defender = WarriorFactory.build(faction=defending_faction)

    result = handle_create_skirmish_for_attack(
        context=FactionWasAttacked(
            attacking_faction=attacking_faction,
            defending_faction=defending_faction,
            attacking_warriors=[attacker],
            defending_warriors=[defender],
            fortification_strength=20,
            month=3,
        )
    )

    assert result == CreateSkirmish(
        name="Attack on Wessex",
        faction_1=attacking_faction,
        faction_2=defending_faction,
        warrior_list_1=[attacker],
        warrior_list_2=[defender],
        month=3,
        fortification_strength=20,
    )


def test_handle_attacker_defender_decided_carries_the_initiative_to_the_blow():
    skirmish = SkirmishFactory.build()
    attacker = WarriorFactory.build()
    defender = WarriorFactory.build()

    result = handle_attacker_defender_decided(
        context=AttackerDefenderDecided(
            skirmish=skirmish,
            round_number=2,
            attacker=attacker,
            attacker_action=SkirmishActionChoices.SIMPLE_ATTACK,
            defender=defender,
            defender_action=SkirmishActionChoices.DEFENSIVE_STANCE,
            initiative=InitiativeChoices.INITIATIVE_UNOPPOSED,
        )
    )

    assert result == WarriorAttacksWarrior(
        skirmish=skirmish,
        round_number=2,
        attacker=attacker,
        attacker_action=SkirmishActionChoices.SIMPLE_ATTACK,
        defender=defender,
        defender_action=SkirmishActionChoices.DEFENSIVE_STANCE,
        initiative=InitiativeChoices.INITIATIVE_UNOPPOSED,
    )


@pytest.mark.django_db
def test_handle_round_finished_wins_the_skirmish_for_the_victor():
    skirmish = SkirmishFactory()

    result = handle_round_finished(
        context=RoundFinished(skirmish=skirmish, round_number=1, victor=skirmish.attacking_faction, month=3)
    )

    assert result == WinSkirmish(skirmish=skirmish, victorious_faction=skirmish.attacking_faction, month=3)


@pytest.mark.django_db
def test_handle_round_finished_does_nothing_without_a_victor():
    skirmish = SkirmishFactory()

    result = handle_round_finished(context=RoundFinished(skirmish=skirmish, round_number=1, victor=None, month=3))

    assert result is None
