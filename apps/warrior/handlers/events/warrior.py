from queuebie import message_registry

from apps.skirmish.messages.events.warrior import WarriorWasKilled


@message_registry.register_event(event=WarriorWasKilled)
def handle_free_items_on_warrior_death(*, context: WarriorWasKilled):
    # TODO: move this to manager
    # TODO: should this be a command instead of handling it here?
    context.warrior.weapon = None
    context.warrior.armor = None
    context.warrior.save()
