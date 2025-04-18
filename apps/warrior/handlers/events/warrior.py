from queuebie import message_registry
from queuebie.messages import Command

from apps.skirmish.messages.events.warrior import WarriorWasKilled
from apps.warrior.messages.commands.warrior import DropWarriorItems


@message_registry.register_event(event=WarriorWasKilled)
def handle_free_items_on_warrior_death(*, context: WarriorWasKilled) -> Command:
    return DropWarriorItems(skirmish=context.skirmish, warrior=context.warrior)
