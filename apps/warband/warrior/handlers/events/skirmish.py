from queuebie import message_registry
from queuebie.messages import Command

from apps.warband.skirmish.messages.events.warrior import WarriorImprovedStats
from apps.warband.warrior.messages.commands.warrior import AwardEarnedNickname


@message_registry.register_event(event=WarriorImprovedStats)
def handle_level_up_earns_a_nickname(*, context: WarriorImprovedStats) -> Command:
    """
    A level raises all four attributes at once, which is the other place a man can first become worth
    naming.

    The month comes off the fight rather than off the message: nothing in a level-up chain carries one,
    and the skirmish it happened in already knows which month it belongs to. Reading it is an attribute
    access on an instance the event carries, not a query.
    """
    return AwardEarnedNickname(warrior=context.warrior, month=context.skirmish.month)
