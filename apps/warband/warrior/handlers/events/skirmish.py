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

    A plain relay, carrying nothing it has to look up. The month comes off the fight the way the
    nickname handler above takes it - an attribute access on an instance the event carries. His
    faction pointedly does not: "reduce_current_health" refreshes the warrior from the database one
    handler earlier, which drops every cached relation on him, so "warrior.faction" here is a query
    in the one place strict mode forbids one. The command's handler reads it instead.
    """
    return InflictInjury(
        skirmish=context.skirmish,
        warrior=context.warrior,
        overkill_health=context.overkill_health,
        month=context.skirmish.month,
    )
