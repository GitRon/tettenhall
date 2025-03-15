from queuebie import message_registry
from queuebie.messages import Command

from apps.faction.messages.commands.faction import AddWarriorToPub, SetNewLeaderWarrior
from apps.warrior.messages.events.warrior import NewLeaderWarriorCreated, WarriorCreated


@message_registry.register_event(event=NewLeaderWarriorCreated)
def handle_set_new_leader_for_faction(*, context: NewLeaderWarriorCreated) -> Command:
    return SetNewLeaderWarrior(faction=context.faction, warrior=context.warrior)


@message_registry.register_event(event=WarriorCreated)
def handle_add_new_warrior_to_faction_pub(*, context: WarriorCreated) -> Command:
    return AddWarriorToPub(faction=context.faction, warrior=context.warrior, month=context.month)
