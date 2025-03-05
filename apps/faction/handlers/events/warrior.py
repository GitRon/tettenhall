from queuebie import message_registry
from queuebie.messages import Command

from apps.faction.messages.commands.faction import SetNewLeaderWarrior
from apps.warrior.messages.events.warrior import NewLeaderWarriorCreated


@message_registry.register_event(event=NewLeaderWarriorCreated)
def handle_set_new_leader_for_faction(*, context: NewLeaderWarriorCreated) -> Command:
    return SetNewLeaderWarrior(faction=context.faction, warrior=context.warrior)
