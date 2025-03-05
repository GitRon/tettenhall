from queuebie import message_registry
from queuebie.messages import Command

from apps.faction.messages.events.faction import NewFactionCreated
from apps.warrior.messages.commands.warrior import CreateNewLeaderWarrior


@message_registry.register_event(event=NewFactionCreated)
def handle_create_leader_for_new_faction(*, context: NewFactionCreated) -> Command:
    return CreateNewLeaderWarrior(faction=context.faction)
