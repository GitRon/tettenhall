from apps.core.domain import message_registry
from apps.skirmish.messages.commands import warrior
from apps.skirmish.messages.events.warrior import WarriorWasCaptured
from apps.skirmish.models.faction import Faction


@message_registry.register_command(command=warrior.WarriorIsCaptured)
def handle_warrior_is_captured(context: warrior.WarriorIsCaptured.Context):
    Faction.objects.add_captive(faction=context.capturing_faction, warrior=context.warrior)

    return WarriorWasCaptured.generator(
        context_data={
            "skirmish": context.skirmish,
            "warrior": context.warrior,
            "capturing_faction": context.capturing_faction,
        }
    )
