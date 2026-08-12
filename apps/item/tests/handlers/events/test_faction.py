from apps.faction.messages.events.faction import RequestNewItemForTownShop
from apps.faction.tests.factories.faction import FactionFactory
from apps.item.handlers.events.faction import handle_request_new_item_for_town_shop
from apps.item.messages.commands.item import CreateItem
from apps.item.models.item_type import ItemType
from apps.item.services.generators.item.mercenary import MercenaryItemGenerator


def test_handle_request_new_item_for_town_shop_maps_to_command():
    """
    Pure mapping, so an unsaved faction is enough.

    The handler used to reach through "faction.savegame" here, which is a query whenever that
    relation is not already cached - and strict mode forbids those in an event handler. What keeps
    it from coming back is not this test but CreateItem no longer having a savegame field at all:
    its handler derives one from "faction.savegame_id", so there was never anything to pass.
    """
    faction = FactionFactory.build()

    result = handle_request_new_item_for_town_shop(
        context=RequestNewItemForTownShop(
            faction=faction,
            generator_class=MercenaryItemGenerator,
            item_function=ItemType.FunctionChoices.FUNCTION_WEAPON,
            month=3,
            quality_bonus=2,
        )
    )

    assert result == CreateItem(
        owner=None,
        faction=faction,
        generator_class=MercenaryItemGenerator,
        item_function=ItemType.FunctionChoices.FUNCTION_WEAPON,
        month=3,
        quality_bonus=2,
    )
