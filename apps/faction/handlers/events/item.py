from queuebie import message_registry
from queuebie.messages import Command

from apps.faction.messages.commands.faction import AddItemToTownShop
from apps.item.messages.events.item import ItemCreated


@message_registry.register_event(event=ItemCreated)
def handle_item_created_for_shop(*, context: ItemCreated) -> Command | None:
    if context.owner is None:
        return AddItemToTownShop(faction=context.faction, item=context.item, month=context.month)

    return None
