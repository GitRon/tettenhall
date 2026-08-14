import pytest
from queuebie.runner import handle_message

from apps.faction.messages.commands.faction import DefeatFactionOfLostLeader
from apps.faction.tests.factories.faction import FactionFactory
from apps.savegame.models.savegame import Savegame
from apps.savegame.tests.factories.savegame import SavegameFactory
from apps.skirmish.models.warrior import Warrior
from apps.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_losing_the_leader_ends_the_game_and_decides_the_open_fight(queuebie_registry):
    """
    The only level that proves the defeat chain: strict mode's database blocker is applied by
    handle_message(), so calling these handlers directly - which every unit test around them does -
    switches the one guard that catches a relation being reached inside an event handler off.

    It is dispatched from the command rather than from a real round because a leader dying is decided
    by the dice, and pinning that would mock the combat this is meant to run for real. Everything from
    here on is the production chain, event handlers and blocker included.
    """
    savegame = SavegameFactory()
    player_faction = FactionFactory(savegame=savegame)
    savegame.player_faction = player_faction
    savegame.save()
    rival_faction = FactionFactory(savegame=savegame)

    leader = WarriorFactory(faction=player_faction, savegame=savegame)
    player_faction.leader = leader
    player_faction.save()

    # The fight he fell in is still running, so ending the game has to decide it
    skirmish = SkirmishFactory(attacking_faction=player_faction, defending_faction=rival_faction)
    skirmish.attacking_warriors.add(leader)
    skirmish.defending_warriors.add(WarriorFactory(faction=rival_faction, savegame=savegame))

    handle_message(DefeatFactionOfLostLeader(warrior=leader))

    savegame.refresh_from_db()
    assert savegame.outcome == Savegame.OutcomeChoices.OUTCOME_LOST
    skirmish.refresh_from_db()
    assert skirmish.victorious_faction == rival_faction


@pytest.mark.django_db
def test_a_warrior_in_two_open_fights_is_taken_prisoner_only_once(queuebie_registry):
    """
    Ending the game decides every unresolved skirmish in one pass, so a warrior standing on two
    rosters is processed as a casualty twice. He used to end up in both victors' cells at once.

    A flow test rather than a unit test because that is the whole defect: the capture handler is
    correct on its own and only misbehaves when the force-resolve above it calls it a second time.
    """
    savegame = SavegameFactory()
    player_faction = FactionFactory(savegame=savegame)
    savegame.player_faction = player_faction
    savegame.save()
    first_rival = FactionFactory(savegame=savegame)
    second_rival = FactionFactory(savegame=savegame)

    leader = WarriorFactory(
        faction=player_faction, savegame=savegame, condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS
    )
    player_faction.leader = leader
    player_faction.save()

    # He was committed to both fights, and neither has been played out
    first_skirmish = SkirmishFactory(attacking_faction=player_faction, defending_faction=first_rival)
    first_skirmish.attacking_warriors.add(leader)
    first_skirmish.defending_warriors.add(WarriorFactory(faction=first_rival, savegame=savegame))
    second_skirmish = SkirmishFactory(attacking_faction=player_faction, defending_faction=second_rival)
    second_skirmish.attacking_warriors.add(leader)
    second_skirmish.defending_warriors.add(WarriorFactory(faction=second_rival, savegame=savegame))

    handle_message(DefeatFactionOfLostLeader(warrior=leader))

    assert list(first_rival.captured_warriors.all()) == [leader]
    assert list(second_rival.captured_warriors.all()) == []


@pytest.mark.django_db
def test_losing_the_last_rival_wins_the_game(queuebie_registry):
    savegame = SavegameFactory()
    player_faction = FactionFactory(savegame=savegame)
    savegame.player_faction = player_faction
    savegame.save()
    rival_faction = FactionFactory(savegame=savegame)

    leader = WarriorFactory(faction=rival_faction, savegame=savegame, condition=Warrior.ConditionChoices.CONDITION_DEAD)
    rival_faction.leader = leader
    rival_faction.save()

    handle_message(DefeatFactionOfLostLeader(warrior=leader))

    savegame.refresh_from_db()
    assert savegame.outcome == Savegame.OutcomeChoices.OUTCOME_WON
    rival_faction.refresh_from_db()
    assert rival_faction.is_defeated is True
