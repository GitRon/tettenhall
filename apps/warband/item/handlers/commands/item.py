from queuebie import message_registry
from queuebie.messages import Event

from apps.warband.finance.models import Transaction
from apps.warband.item.messages.commands import item
from apps.warband.item.messages.events.item import (
    ItemBought,
    ItemCreated,
    ItemEquipped,
    ItemSold,
    ItemWasLost,
    OwnershipChanged,
)
from apps.warband.item.models.item import Item
from apps.warband.item.services.sale import get_sell_payout
from apps.warband.skirmish.models import Warrior


@message_registry.register_command(command=item.CreateItem)
def handle_create_item(*, context: item.CreateItem) -> list[Event] | Event:
    generator = context.generator_class(
        faction=context.owner,
        item_function=context.item_function,
        savegame_id=context.faction.savegame_id,
        quality_bonus=context.quality_bonus,
    )

    new_item = generator.process()

    return ItemCreated(
        owner=context.owner,
        faction=context.faction,
        item=new_item,
        month=context.month,
    )


@message_registry.register_command(command=item.SellItem)
def handle_sell_item(*, context: item.SellItem) -> list[Event] | Event | None:
    # Only while he still owns it: the second of two overlapping requests finds it sold already, and
    # would otherwise be paid for it again
    if not Item.objects.hand_over(item=context.item, previous_owner=context.selling_faction, new_owner=None):
        return None

    # The item keeps its list price and goes back on the shelf at it, so a poor market means selling
    # something and buying it back is a loss
    return ItemSold(
        selling_faction=context.selling_faction,
        item=context.item,
        item_name=context.item.display_name,
        price=get_sell_payout(item=context.item, faction=context.selling_faction),
        month=context.month,
    )


@message_registry.register_command(command=item.BuyItem)
def handle_buy_item(*, context: item.BuyItem) -> list[Event] | Event | None:
    # Only while the purse still covers it: two different purchases can each pass the view's check on
    # the same balance, and only the one that gets the write lock first may spend it
    if Transaction.objects.current_balance(faction_id=context.buying_faction.id) < context.price:
        return None

    # Only while it is still unowned stock: the second of two overlapping requests finds it bought
    # already, and would otherwise be charged for it again
    if not Item.objects.hand_over(item=context.item, previous_owner=None, new_owner=context.buying_faction):
        return None

    return ItemBought(
        buying_faction=context.buying_faction,
        item=context.item,
        item_name=context.item.display_name,
        price=context.price,
        month=context.month,
    )


@message_registry.register_command(command=item.LoseItem)
def handle_lose_item(*, context: item.LoseItem) -> list[Event] | Event:
    """
    Take a piece of gear out of the game.

    Off the man carrying it first: the row is about to go, and a warrior left pointing at nothing is
    a warrior fighting with a null weapon. Its name is read before the delete, because deleting an
    instance clears the primary key its display name is assembled from.
    """
    item_name = context.item.display_name

    Warrior.objects.take_item_away(item=context.item)
    context.item.delete()

    return ItemWasLost(faction=context.faction, item_name=item_name, month=context.month)


@message_registry.register_command(command=item.ChangeOwnership)
def handle_change_ownership(*, context: item.ChangeOwnership) -> list[Event] | Event:
    # Take item away from previous owner
    Warrior.objects.take_item_away(item=context.item)

    # Set ownership in the item itself, so it belongs to the winning faction
    Item.objects.update_ownership(item=context.item, new_owner=context.new_owner)

    return OwnershipChanged(
        previous_owner=context.previous_owner,
        item=context.item,
        new_owner=context.new_owner,
    )


@message_registry.register_command(command=item.EquipItem)
def handle_equip_item(*, context: item.EquipItem) -> list[Event] | Event:
    """
    Hand a warrior a piece of gear, off whoever is carrying it.

    When both slots are full the two men exchange rather than the other being left empty-handed: the
    move this exists for is passing a better weapon down a line, and a swap is the shape of that
    which never disarms somebody the player is not looking at.

    Both slots are emptied in one statement before either is filled. The slot is a "OneToOneField",
    so between the two writes of a swap there is a moment when one item would be claimed by two
    warriors, and the unique index refuses exactly that.

    Who holds what is read off the rows, not off the instances on the message. A rival's handout queues
    a line of these, and an instance loaded before the first of them ran still names the man an item
    was taken off as its holder - which would empty his slot a second time.
    """
    context.warrior.refresh_from_db(fields=(context.slot,))
    previous_holder = (
        Warrior.objects.filter(**{context.slot: context.item}).first() if context.item is not None else None
    )
    displaced_item = getattr(context.warrior, context.slot)

    # The slot saved on what was already in it. Nothing moves, and both ends of the move have to fall
    # away rather than naming this man as the one the item was taken off and handed back to.
    if displaced_item == context.item:
        previous_holder = None
        displaced_item = None

    warrior_ids = [context.warrior.id] + ([previous_holder.id] if previous_holder else [])
    Warrior.objects.filter(id__in=warrior_ids).update(**{context.slot: None})

    setattr(context.warrior, context.slot, context.item)
    context.warrior.save(update_fields=(context.slot,))

    # Only if he has a free hand to put it in - which is his own slot, emptied a moment ago. Nothing
    # comes back the other way when the receiving slot was empty, and the item is simply his now.
    if previous_holder and displaced_item:
        setattr(previous_holder, context.slot, displaced_item)
        previous_holder.save(update_fields=(context.slot,))

    return ItemEquipped(
        warrior=context.warrior,
        item=context.item,
        slot=context.slot,
        previous_holder=previous_holder,
        displaced_item=displaced_item,
    )
