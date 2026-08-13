import pytest

from apps.faction.tests.factories.faction import FactionFactory
from apps.skirmish.handlers.events.skirmish import handle_create_skirmish_for_attack, handle_round_finished
from apps.skirmish.messages.commands.skirmish import CreateSkirmish, WinSkirmish
from apps.skirmish.messages.events.skirmish import FactionWasAttacked, RoundFinished
from apps.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.skirmish.tests.factories.warrior import WarriorFactory


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
        quest_contract=None,
    )


@pytest.mark.django_db
def test_handle_round_finished_wins_the_skirmish_for_the_victor():
    skirmish = SkirmishFactory()

    result = handle_round_finished(context=RoundFinished(skirmish=skirmish, victor=skirmish.player_faction, month=3))

    assert result == WinSkirmish(skirmish=skirmish, victorious_faction=skirmish.player_faction, month=3)


@pytest.mark.django_db
def test_handle_round_finished_does_nothing_without_a_victor():
    skirmish = SkirmishFactory()

    result = handle_round_finished(context=RoundFinished(skirmish=skirmish, victor=None, month=3))

    assert result is None
