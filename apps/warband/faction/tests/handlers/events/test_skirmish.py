from apps.warband.faction.handlers.events.skirmish import (
    handle_defeat_faction_of_a_lost_leader,
    handle_village_burned_thins_the_fyrd,
)
from apps.warband.faction.messages.commands.faction import ChangeFyrdReserve, DefeatFactionOfLostLeader
from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.skirmish.messages.events.skirmish import VillageBurned
from apps.warband.skirmish.messages.events.warrior import WarriorWasCaptured, WarriorWasKilled
from apps.warband.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory


def test_handle_defeat_faction_of_a_lost_leader_for_a_killed_warrior():
    warrior = WarriorFactory.build()

    result = handle_defeat_faction_of_a_lost_leader(
        context=WarriorWasKilled(skirmish=SkirmishFactory.build(), warrior=warrior, by_warrior=WarriorFactory.build())
    )

    assert result == DefeatFactionOfLostLeader(warrior=warrior)


def test_handle_defeat_faction_of_a_lost_leader_for_a_captured_warrior():
    """
    One test per registered message: the two events carry different extra fields, and reading either
    of them here would only fail once the other one is dispatched.
    """
    warrior = WarriorFactory.build()

    result = handle_defeat_faction_of_a_lost_leader(
        context=WarriorWasCaptured(
            skirmish=SkirmishFactory.build(), warrior=warrior, capturing_faction=FactionFactory.build()
        )
    )

    assert result == DefeatFactionOfLostLeader(warrior=warrior)


def test_handle_defeat_faction_of_a_lost_leader_for_an_occupation_allows_no_successor():
    """
    A capture with no skirmish is the one an occupation makes: the town is taken with the leader.
    """
    warrior = WarriorFactory.build()

    result = handle_defeat_faction_of_a_lost_leader(
        context=WarriorWasCaptured(skirmish=None, warrior=warrior, capturing_faction=FactionFactory.build())
    )

    assert result == DefeatFactionOfLostLeader(warrior=warrior, allow_succession=False)


def test_handle_village_burned_thins_the_fyrd_strikes_the_names_off_the_reserve():
    raided_faction = FactionFactory.build()

    result = handle_village_burned_thins_the_fyrd(
        context=VillageBurned(
            skirmish=SkirmishFactory.build(),
            raiding_faction=FactionFactory.build(),
            raided_faction=raided_faction,
            fyrd_names=2,
            month=4,
        )
    )

    assert result == ChangeFyrdReserve(faction=raided_faction, change=-2, month=4)
