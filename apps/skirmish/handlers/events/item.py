from queuebie import message_registry
from queuebie.messages import Command

from apps.skirmish.messages.commands.item import WarriorDropsLoot
from apps.skirmish.messages.commands.transaction import WarriorDropsSilver
from apps.skirmish.messages.events import skirmish


@message_registry.register_event(event=skirmish.SkirmishFinished)
def handle_distribute_loot(*, context: skirmish.SkirmishFinished) -> list[Command]:
    message_list = []

    for warrior in context.incapacitated_warriors:
        # Reassign items
        message_list.append(
            WarriorDropsLoot(
                skirmish=context.skirmish,
                warrior=warrior,
                new_owner=context.skirmish.victorious_faction,
            )
        )
        # Give out money
        message_list.append(
            WarriorDropsSilver(
                skirmish=context.skirmish,
                warrior=warrior,
                gaining_faction=context.skirmish.victorious_faction,
                month=context.month,
            )
        )

    return message_list
