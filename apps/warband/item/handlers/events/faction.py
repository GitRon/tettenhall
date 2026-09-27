from queuebie import message_registry
from queuebie.messages import Command

from apps.warband.faction.messages.events.faction import NewFactionCreated
from apps.warband.faction.messages.events.item import RequestNewItemForTownShop
from apps.warband.item.messages.commands.item import CreateItem
from apps.warband.item.models.item_type import ItemType
from apps.warband.item.services.generators.item.fyrd import FyrdItemGenerator

# Added to the fyrd's modifier roll for the gear a new war band finds in its stores. The fyrd's condition
# thresholds stay on its own mean, so this pushes most of it down to Rusty or Cheap: worse on average than
# what a levy brings from the fields, and well below a mercenary's kit or the leader's.
STARTING_GEAR_QUALITY_BONUS = -2


@message_registry.register_event(event=RequestNewItemForTownShop)
def handle_request_new_item_for_town_shop(*, context: RequestNewItemForTownShop) -> Command:
    return CreateItem(
        owner=None,
        faction=context.faction,
        item_function=context.item_function,
        generator_class=context.generator_class,
        month=context.month,
        quality_bonus=context.quality_bonus,
    )


@message_registry.register_event(event=NewFactionCreated)
def handle_stock_starting_gear_for_player_faction(*, context: NewFactionCreated) -> list[Command] | None:
    """
    One poor weapon and one poor piece of armour in the player's stores, so month one opens with gear to
    hand out or sell rather than an empty shelf.

    A fixed pair rather than a roll: both slots get a decision, and every savegame opens the same way.
    The player's alone - a rival's stores are never opened by anybody, and free gear would only change
    its fights.
    """
    if not context.is_player:
        return None

    return [
        CreateItem(
            owner=context.faction,
            faction=context.faction,
            generator_class=FyrdItemGenerator,
            item_function=item_function,
            month=context.current_month,
            quality_bonus=STARTING_GEAR_QUALITY_BONUS,
        )
        for item_function in (ItemType.FunctionChoices.FUNCTION_WEAPON, ItemType.FunctionChoices.FUNCTION_ARMOR)
    ]
