from apps.core.domain import message_registry
from apps.faction.messages.events.faction import FactionWarriorsWithLowMoraleDetermined
from apps.warrior.messages.commands.warrior import ReplenishWarriorMorale


@message_registry.register_event(event=FactionWarriorsWithLowMoraleDetermined)
def handle_warriors_with_low_morale_determined(context: FactionWarriorsWithLowMoraleDetermined.Context):
    event_list = []
    for warrior in context.warrior_list:
        event_list.append(
            ReplenishWarriorMorale.generator(
                context_data={
                    "warrior": warrior,
                    "week": context.week,
                }
            )
        )
    return event_list
