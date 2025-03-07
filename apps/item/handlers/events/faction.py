from queuebie import message_registry
from queuebie.messages import Command

from apps.faction.messages.events.faction import RequestNewItemForTownShop
from apps.item.messages.commands.item import CreateItem


@message_registry.register_event(event=RequestNewItemForTownShop)
def handle_request_new_item_for_town_shop(*, context: RequestNewItemForTownShop) -> Command:
    return CreateItem(
        owner=None,
        faction=context.faction,
        savegame=context.faction.savegame,
        item_function=context.item_function,
        generator_class=context.generator_class,
        month=context.month,
    )
