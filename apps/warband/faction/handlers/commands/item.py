import random

from queuebie import message_registry
from queuebie.messages import Event

from apps.warband.faction.messages.commands.item import (
    AddItemToTownShop,
    HandOutFactionGear,
    RemoveItemFromTownShop,
    RestockTownShopItems,
)
from apps.warband.faction.messages.events.item import (
    GearHandoutApproved,
    ItemWasAddedToShop,
    ItemWasRemovedFromShop,
    RequestNewItemForTownShop,
    TownShopRestocked,
)
from apps.warband.item.models import ItemType
from apps.warband.item.services.generators.item.mercenary import MercenaryItemGenerator
from apps.warband.item.services.handout import plan_gear_handout
from apps.warband.town.buildings.marketplace import Marketplace
from apps.warband.town.buildings.weaponsmith import Weaponsmith


def _draw_stall_functions(*, stall_count: int) -> list[ItemType.FunctionChoices]:
    """
    What each of the month's stalls sells, one entry per stall.

    A shop of one kind is a shop the player has no decision to make in, and an independent coin flip
    per stall reaches that often: three stalls is the smallest market in the game and comes out all
    weapons or all armour a quarter of the time. So a market holding two or more stalls always sells
    at least one of each, and only the stalls beyond the second are flipped for.

    Shuffled afterwards, because the pair would otherwise always be the first two items on the shelf:
    an item carries no ordering of its own, so the order they are asked for in is the order the
    player reads them in.
    """
    weapon = ItemType.FunctionChoices.FUNCTION_WEAPON
    armor = ItemType.FunctionChoices.FUNCTION_ARMOR

    # Sliced rather than guarded, so a market too small to hold both simply gets what fits
    stall_functions = [weapon, armor][:stall_count]
    stall_functions += [
        weapon if bool(random.getrandbits(1)) else armor for _ in range(stall_count - len(stall_functions))
    ]
    random.shuffle(stall_functions)

    return stall_functions


@message_registry.register_command(command=RestockTownShopItems)
def handle_restock_shop_items(*, context: RestockTownShopItems) -> list[Event] | Event:
    # Clean up previous stock, all but what has just been bought: a purchase hands the item over in its
    # own command, but takes it off the shelf an event later, which can be after this has run
    context.faction.available_items.filter(owner__isnull=True).delete()

    message_list = []

    # The market decides how many stalls there are, the weaponsmith how good their wares
    marketplace = Marketplace.get_building_by_type(building_type=context.faction.town.marketplace)
    weaponsmith = Weaponsmith.get_building_by_type(building_type=context.faction.town.weaponsmith)

    # The shop borrows the mercenary generator for its modifier distribution only. Which bands it stocks
    # is the weaponsmith's: the shop is where a player buys his way up, and the forge is what opens the
    # way, so its pool is passed in rather than inherited from the archetype
    for item_function in _draw_stall_functions(stall_count=marketplace.AVAILABLE_ITEMS):
        message_list.append(
            RequestNewItemForTownShop(
                faction=context.faction,
                generator_class=MercenaryItemGenerator,
                item_function=item_function,
                month=context.month,
                quality_bonus=weaponsmith.QUALITY_BONUS,
                item_tiers=weaponsmith.SHOP_ITEM_TIERS,
            )
        )

    # After the loop, and counting the whole shop rather than each item: the player wants to know
    # whether it is worth walking over, not that a stall was filled
    message_list.append(
        TownShopRestocked(faction=context.faction, new_items=marketplace.AVAILABLE_ITEMS, month=context.month)
    )

    return message_list


# What the shop holds is the faction's "available_items" and nothing else - see ItemQuerySet.on_sale_at,
# which is the other end of the same rule. Who owns an item is a separate fact the "item" package keeps,
# through Item.objects.update_ownership(), and it already says the right thing by the time either of
# these two commands is dispatched: shop stock is generated unowned, a sale drops the owner before it
# announces itself, and a purchase sets him.
@message_registry.register_command(command=AddItemToTownShop)
def handle_add_item_to_shop(*, context: AddItemToTownShop) -> list[Event] | Event:
    context.faction.available_items.add(context.item)

    return ItemWasAddedToShop(faction=context.faction, item=context.item, month=context.month)


@message_registry.register_command(command=RemoveItemFromTownShop)
def handle_buy_item_for_faction(*, context: RemoveItemFromTownShop) -> Event:
    context.faction.available_items.remove(context.item)

    return ItemWasRemovedFromShop(faction=context.faction, item=context.item, month=context.month)


@message_registry.register_command(command=HandOutFactionGear)
def handle_hand_out_faction_gear(*, context: HandOutFactionGear) -> list[Event]:
    """
    Which of a rival's items go on which of its men - see [plan_gear_handout] for who gets what.

    Shaped like [handle_plan_faction_month]: this decides and writes nothing, and each equip it settles
    on goes out as an approval that becomes the same "EquipItem" the player's own handout dispatches.
    The player is refused, because choosing who carries what is his to do.

    Asked again every time something it depends on changes, so two askings can land in one drain and
    both be planned on the same state. The second then only approves what the first already did, and
    each of those equips finds the item in the slot already and moves nothing.
    """
    if context.faction.savegame.player_faction_id == context.faction.id:
        return []

    return [
        GearHandoutApproved(faction=context.faction, warrior=warrior, item=item, slot=slot)
        for warrior, item, slot in plan_gear_handout(faction=context.faction)
    ]
