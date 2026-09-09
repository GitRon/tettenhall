from apps.warband.faction.handlers.events.skirmish import handle_defeat_faction_of_a_lost_leader
from apps.warband.faction.messages.commands.faction import DefeatFactionOfLostLeader
from apps.warband.faction.tests.factories.faction import FactionFactory
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
