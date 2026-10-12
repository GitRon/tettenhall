from queuebie import message_registry
from queuebie.messages import Command

from apps.warband.skirmish.messages.commands.item import WarriorDropsLoot
from apps.warband.skirmish.messages.commands.transaction import WarriorDropsSilver
from apps.warband.skirmish.messages.events import skirmish


@message_registry.register_event(event=skirmish.SkirmishFinished)
def handle_distribute_loot(*, context: skirmish.SkirmishFinished) -> list[Command]:
    messages = []

    for warrior in context.incapacitated_warriors:
        # Reassign items
        messages.append(
            WarriorDropsLoot(
                skirmish=context.skirmish,
                warrior=warrior,
                new_owner=context.skirmish.victorious_faction,
            )
        )
        # Give out money
        messages.append(
            WarriorDropsSilver(
                skirmish=context.skirmish,
                warrior=warrior,
                gaining_faction=context.skirmish.victorious_faction,
                month=context.month,
            )
        )

    return messages
