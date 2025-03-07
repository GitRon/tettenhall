from queuebie import message_registry
from queuebie.messages import Command

from apps.faction.messages.events.faction import NewFactionCreated
from apps.faction.messages.events.warrior import RequestWarriorForPub
from apps.warrior.messages.commands.warrior import CreateNewLeaderWarrior, CreateWarrior


@message_registry.register_event(event=NewFactionCreated)
def handle_create_leader_for_new_faction(*, context: NewFactionCreated) -> Command:
    return CreateNewLeaderWarrior(faction=context.faction)


@message_registry.register_event(event=RequestWarriorForPub)
def handle_request_warrior_for_pub(*, context: RequestWarriorForPub) -> Command:
    return CreateWarrior(
        faction=context.faction,
        culture=context.culture,
        generator_class=context.generator_class,
        month=context.month,
    )
