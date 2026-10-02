from queuebie import message_registry
from queuebie.messages import Command

from apps.warband.faction.messages.commands.faction import ChangeFyrdReserve, DefeatFactionOfLostLeader
from apps.warband.skirmish.messages.events import skirmish, warrior


@message_registry.register_event(event=warrior.WarriorWasCaptured)
@message_registry.register_event(event=warrior.WarriorWasKilled)
def handle_defeat_faction_of_a_lost_leader(
    *,
    context: warrior.WarriorWasKilled | warrior.WarriorWasCaptured,
) -> Command:
    """
    Losing the leader costs his faction its leader, whether he fell or was taken - a successor if there
    is one, the game if there is not.

    Whether this warrior led anyone is a question for the database, and strict mode blocks that here,
    so the command handler asks it. Only "warrior" and "skirmish" are read because they are the fields
    both events carry - "by_warrior" is on the kill, "capturing_faction" on the capture.

    A capture with no skirmish is an occupation: the town was ridden into, and a faction that has lost
    its town has nobody left to rally round a successor.
    """
    return DefeatFactionOfLostLeader(warrior=context.warrior, allow_succession=context.skirmish is not None)


@message_registry.register_event(event=skirmish.VillageBurned)
def handle_village_burned_thins_the_fyrd(*, context: skirmish.VillageBurned) -> Command:
    # The men the village would have sent are gone with it, so the reserve loses them the way a draft
    # takes them: the names are struck off, and the next draft finds fewer to call
    return ChangeFyrdReserve(faction=context.raided_faction, change=-context.fyrd_names, month=context.month)
