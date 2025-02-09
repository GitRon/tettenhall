import random

from queuebie import message_registry
from queuebie.messages import Event

from apps.item.models.item_type import ItemType
from apps.item.services.generators.item.mercenary import MercenaryItemGenerator
from apps.marketplace.messages.commands.item import RestockMarketplaceItems
from apps.marketplace.messages.events.item import MarketplaceItemsRestocked


@message_registry.register_command(command=RestockMarketplaceItems)
def handle_restock_marketplace_items(*, context: RestockMarketplaceItems) -> list[Event] | Event:
    # Clean up previous stock
    context.marketplace.available_items.all().delete()

    no_items = random.randrange(4, 6)
    for _ in range(no_items):
        if bool(random.getrandbits(1)):
            item_generator = MercenaryItemGenerator(
                faction=None,
                item_function=ItemType.FunctionChoices.FUNCTION_WEAPON,
                savegame_id=context.marketplace.savegame.id,
            )
        else:
            item_generator = MercenaryItemGenerator(
                faction=None,
                item_function=ItemType.FunctionChoices.FUNCTION_ARMOR,
                savegame_id=context.marketplace.savegame.id,
            )

        item = item_generator.process()
        context.marketplace.available_items.add(item)

    return MarketplaceItemsRestocked(marketplace=context.marketplace, month=context.month)
