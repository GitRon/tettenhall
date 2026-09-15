from queuebie import message_registry
from queuebie.messages import Command

from apps.warband.skirmish.messages.events.warrior import WarriorImprovedStats, WarriorWasIncapacitated
from apps.warband.warrior.messages.commands.warrior import AwardEarnedNickname, InflictInjury


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


@message_registry.register_event(event=WarriorWasIncapacitated)
def handle_beating_may_leave_a_mark(*, context: WarriorWasIncapacitated) -> Command:
    """
    A man beaten senseless is the one moment the game can ask whether he keeps anything.

    Read at the end of the blow rather than off the blow record, because the fight has already decided
    what going down means and a second threshold would be a competing definition of it.

    The faction comes off the warrior, which is free here: he is knocked out during the fight and
    taken prisoner only once it is decided, so his own FK still stands. The month comes off the fight
    the way the nickname handler above takes it - an attribute access on an instance the event
    carries, not a query.
    """
    return InflictInjury(
        skirmish=context.skirmish,
        warrior=context.warrior,
        faction=context.warrior.faction,
        overkill_health=context.overkill_health,
        month=context.skirmish.month,
    )
