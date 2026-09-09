from apps.warband.faction.messages.events.faction import FactionWasOccupied
from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.skirmish.handlers.events.faction import handle_seize_leader_of_occupied_faction
from apps.warband.skirmish.messages.commands.warrior import CaptureWarrior
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory


def test_handle_seize_leader_of_occupied_faction_takes_him_without_a_skirmish():
    occupying_faction = FactionFactory.build()
    faction = FactionFactory.build()
    leader = WarriorFactory.build(faction=faction)

    result = handle_seize_leader_of_occupied_faction(
        context=FactionWasOccupied(
            faction=faction,
            occupying_faction=occupying_faction,
            leader=leader,
            plundered_silver=400,
            month=3,
        )
    )

    assert result == CaptureWarrior(skirmish=None, warrior=leader, capturing_faction=occupying_faction)
