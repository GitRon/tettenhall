from queuebie import message_registry
from queuebie.messages import Event

from apps.faction.messages.commands.item import AddItemToTownShop, RemoveItemFromTownShop
from apps.faction.messages.events.item import ItemWasAddedToShop, ItemWasRemovedFromShop


@message_registry.register_command(command=AddItemToTownShop)
def handle_add_item_to_shop(*, context: AddItemToTownShop) -> list[Event] | Event:
    context.faction.available_items.add(context.item)

    return ItemWasAddedToShop(faction=context.faction, item=context.item, month=context.month)


@message_registry.register_command(command=RemoveItemFromTownShop)
def handle_buy_item_for_faction(*, context: RemoveItemFromTownShop) -> Event:
    context.faction.available_items.add(context.item)

    return ItemWasRemovedFromShop(faction=context.faction, item=context.item, month=context.month)


@message_registry.register_command(command=AddItemToTownShop)
def handle_sell_item_from_faction(*, context: AddItemToTownShop) -> Event:
    context.faction.available_items.remove(context.item)

    return ItemWasAddedToShop(faction=context.faction, item=context.item, month=context.month)
