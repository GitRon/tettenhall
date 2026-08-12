from queuebie import message_registry
from queuebie.messages import Command

from apps.faction.messages.commands.faction import DefeatFactionOfLostLeader
from apps.skirmish.messages.events import warrior


@message_registry.register_event(event=warrior.WarriorWasCaptured)
@message_registry.register_event(event=warrior.WarriorWasKilled)
def handle_defeat_faction_of_a_lost_leader(
    *,
    context: warrior.WarriorWasKilled | warrior.WarriorWasCaptured,
) -> Command:
    """
    Losing the leader knocks his faction out, whether he fell or was taken.

    Whether this warrior led anyone is a question for the database, and strict mode blocks that here,
    so the command handler asks it. Only "warrior" is read because it is the one field both events
    carry - "by_warrior" is on the kill, "capturing_faction" on the capture.
    """
    return DefeatFactionOfLostLeader(warrior=context.warrior)
