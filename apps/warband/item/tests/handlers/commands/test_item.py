import pytest

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.finance.tests.factories.transaction import TransactionFactory
from apps.warband.item.handlers.commands.item import (
    handle_buy_item,
    handle_change_ownership,
    handle_create_item,
    handle_equip_item,
    handle_lose_item,
    handle_sell_item,
)
from apps.warband.item.messages.commands.item import (
    BuyItem,
    ChangeOwnership,
    CreateItem,
    EquipItem,
    LoseItem,
    SellItem,
)
from apps.warband.item.messages.events.item import (
    ItemBought,
    ItemCreated,
    ItemEquipped,
    ItemSold,
    ItemWasLost,
    OwnershipChanged,
)
from apps.warband.item.models.item import Item
from apps.warband.item.models.item_type import ItemType
from apps.warband.item.services.generators.item.fyrd import FyrdItemGenerator
from apps.warband.item.tests.factories.item import ItemFactory
from apps.warband.item.tests.factories.item_type import ItemTypeFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_handle_sell_item_pays_out_the_share_the_market_fetches():
    """
    Selling used to pay the full list price, which the item keeps and goes back on the shelf at - so
    selling and buying the same item back was free.
    """
    # A trading post fetches 70% of the list price
    faction = FactionFactory(town__marketplace=2)
    item = ItemFactory(savegame=faction.savegame, owner=faction, price=200)

    result = handle_sell_item(context=SellItem(selling_faction=faction, item=item, month=3))

    assert result == ItemSold(selling_faction=faction, item=item, item_name=item.display_name, price=140, month=3)
    item.refresh_from_db()
    assert item.owner is None


@pytest.mark.django_db
def test_handle_sell_item_without_a_market_of_its_own():
    faction = FactionFactory()
    item = ItemFactory(savegame=faction.savegame, owner=faction, price=200)

    result = handle_sell_item(context=SellItem(selling_faction=faction, item=item, month=3))

    # Fleeced down to 40% without a market
    assert result.price == 80


@pytest.mark.django_db
def test_handle_sell_item_rounds_a_half_share_down():
    """
    A float ratio made this depend on binary representation error: 110 * 0.55 is 60.500000000000004
    and rounded up to 61, while 90 * 0.85 is exactly 76.5 and rounded down to 76 - two sales at the
    same advertised share landing on opposite sides of the half.
    """
    faction = FactionFactory(town__marketplace=1)
    item = ItemFactory(savegame=faction.savegame, owner=faction, price=110)

    result = handle_sell_item(context=SellItem(selling_faction=faction, item=item, month=3))

    assert result.price == 60


@pytest.mark.django_db
def test_handle_sell_item_pays_at_least_a_silver():
    """
    Rounding a cheap item's share down reaches zero, which handed the item over for nothing.
    """
    faction = FactionFactory()
    item = ItemFactory(savegame=faction.savegame, owner=faction, price=1)

    result = handle_sell_item(context=SellItem(selling_faction=faction, item=item, month=3))

    assert result.price == 1


@pytest.mark.django_db
def test_handle_sell_item_pays_nothing_for_an_item_already_sold():
    """
    The second of two overlapping requests: both found the item in the faction's stash, and the first
    has already sold it. Paying out again would turn a double click into silver.
    """
    faction = FactionFactory()
    item = ItemFactory(savegame=faction.savegame, owner=faction, price=200)
    stale_item = Item.objects.get(pk=item.pk)
    handle_sell_item(context=SellItem(selling_faction=faction, item=item, month=3))

    result = handle_sell_item(context=SellItem(selling_faction=faction, item=stale_item, month=3))

    assert result is None


@pytest.mark.django_db
def test_handle_buy_item_hands_the_shop_stock_to_the_buyer():
    faction = FactionFactory()
    TransactionFactory(faction=faction, amount=200)
    item = ItemFactory(savegame=faction.savegame, owner=None, price=200)

    result = handle_buy_item(context=BuyItem(buying_faction=faction, item=item, price=200, month=3))

    assert result == ItemBought(buying_faction=faction, item=item, item_name=item.display_name, price=200, month=3)
    item.refresh_from_db()
    assert item.owner == faction


@pytest.mark.django_db
def test_handle_buy_item_leaves_it_on_the_shelf_when_the_purse_no_longer_covers_it():
    """
    Two different purchases, both passed by their views on the same 200 silver. The other one has been
    paid for, so this one has to find a purse that no longer reaches the price.
    """
    faction = FactionFactory()
    TransactionFactory(faction=faction, amount=200)
    TransactionFactory(faction=faction, amount=-150)
    item = ItemFactory(savegame=faction.savegame, owner=None, price=200)

    result = handle_buy_item(context=BuyItem(buying_faction=faction, item=item, price=200, month=3))

    assert result is None
    item.refresh_from_db()
    assert item.owner is None


@pytest.mark.django_db
def test_handle_buy_item_charges_nothing_for_an_item_already_bought():
    """
    The second of two overlapping requests: both found the item on the shelf, and the first has
    already bought it. Charging again would take the price twice for one item.
    """
    faction = FactionFactory()
    TransactionFactory(faction=faction, amount=200)
    item = ItemFactory(savegame=faction.savegame, owner=None, price=200)
    stale_item = Item.objects.get(pk=item.pk)
    handle_buy_item(context=BuyItem(buying_faction=faction, item=item, price=200, month=3))

    result = handle_buy_item(context=BuyItem(buying_faction=faction, item=stale_item, price=200, month=3))

    assert result is None


@pytest.mark.django_db
def test_handle_change_ownership_hands_the_item_to_the_new_faction():
    previous_owner = WarriorFactory()
    item = ItemFactory(savegame=previous_owner.savegame, owner=previous_owner.faction)
    previous_owner.weapon = item
    previous_owner.save()
    new_owner = FactionFactory(savegame=previous_owner.savegame)

    result = handle_change_ownership(
        context=ChangeOwnership(previous_owner=previous_owner, item=item, new_owner=new_owner)
    )

    assert result == OwnershipChanged(previous_owner=previous_owner, item=item, new_owner=new_owner)
    item.refresh_from_db()
    assert item.owner == new_owner


@pytest.mark.django_db
def test_handle_change_ownership_takes_the_item_off_its_wielder():
    previous_owner = WarriorFactory()
    item = ItemFactory(savegame=previous_owner.savegame, owner=previous_owner.faction)
    previous_owner.weapon = item
    previous_owner.save()

    handle_change_ownership(
        context=ChangeOwnership(
            previous_owner=previous_owner, item=item, new_owner=FactionFactory(savegame=previous_owner.savegame)
        )
    )

    previous_owner.refresh_from_db()
    assert previous_owner.weapon is None


@pytest.mark.django_db
def test_handle_lose_item_takes_the_gear_out_of_the_game():
    """
    The name is read before the row goes: deleting an instance clears the primary key its display
    name is assembled from, so an event built afterwards would report a nameless loss.
    """
    faction = FactionFactory()
    item = ItemFactory(savegame=faction.savegame, owner=faction)
    item_name = item.display_name

    result = handle_lose_item(context=LoseItem(faction=faction, item=item, month=3))

    assert result == ItemWasLost(faction=faction, item_name=item_name, month=3)
    assert Item.objects.filter(id=item.id).exists() is False


@pytest.mark.django_db
def test_handle_lose_item_takes_it_off_the_man_carrying_it():
    """
    A warrior left pointing at a deleted row is a warrior fighting with a null weapon.
    """
    warrior = WarriorFactory()
    item = ItemFactory(savegame=warrior.savegame, owner=warrior.faction)
    warrior.weapon = item
    warrior.save()

    handle_lose_item(context=LoseItem(faction=warrior.faction, item=item, month=3))

    warrior.refresh_from_db()
    assert warrior.weapon is None


@pytest.mark.django_db
def test_handle_equip_item_fills_an_empty_slot_from_the_stash():
    warrior = WarriorFactory()
    item = ItemFactory(savegame=warrior.savegame, owner=warrior.faction)

    result = handle_equip_item(context=EquipItem(warrior=warrior, item=item, slot="weapon"))

    assert result == ItemEquipped(warrior=warrior, item=item, slot="weapon", previous_holder=None, displaced_item=None)
    warrior.refresh_from_db()
    assert warrior.weapon == item


@pytest.mark.django_db
def test_handle_equip_item_swaps_when_both_slots_are_full():
    """
    The move this exists for: a better weapon passed down a line, with the old one going back the
    other way rather than the second man being left empty-handed.
    """
    receiver = WarriorFactory()
    holder = WarriorFactory(faction=receiver.faction)
    wanted_item = ItemFactory(savegame=receiver.savegame, owner=receiver.faction)
    held_item = ItemFactory(savegame=receiver.savegame, owner=receiver.faction)
    receiver.weapon = held_item
    receiver.save()
    holder.weapon = wanted_item
    holder.save()

    result = handle_equip_item(context=EquipItem(warrior=receiver, item=wanted_item, slot="weapon"))

    assert result == ItemEquipped(
        warrior=receiver,
        item=wanted_item,
        slot="weapon",
        previous_holder=holder,
        displaced_item=held_item,
    )
    # Both rows, off the database. The event alone would report a swap that only half happened:
    # messages compare by primary key, so "warrior=receiver" says who the move was about and nothing
    # about what he ended up holding.
    receiver.refresh_from_db()
    holder.refresh_from_db()
    assert (receiver.weapon, holder.weapon) == (wanted_item, held_item)


@pytest.mark.django_db
def test_handle_equip_item_leaves_the_previous_holder_empty_handed_when_there_is_nothing_to_give_back():
    receiver = WarriorFactory()
    holder = WarriorFactory(faction=receiver.faction)
    item = ItemFactory(savegame=receiver.savegame, owner=receiver.faction)
    holder.weapon = item
    holder.save()

    result = handle_equip_item(context=EquipItem(warrior=receiver, item=item, slot="weapon"))

    assert result.displaced_item is None
    receiver.refresh_from_db()
    holder.refresh_from_db()
    assert (receiver.weapon, holder.weapon) == (item, None)


@pytest.mark.django_db
def test_handle_equip_item_puts_a_displaced_item_back_in_the_stash():
    """
    Nobody was carrying the new item, so there is no previous holder to hand the old one to and it
    is simply unworn again - which is what puts it back in the faction's unused items.
    """
    warrior = WarriorFactory()
    held_item = ItemFactory(savegame=warrior.savegame, owner=warrior.faction)
    new_item = ItemFactory(savegame=warrior.savegame, owner=warrior.faction)
    warrior.weapon = held_item
    warrior.save()

    result = handle_equip_item(context=EquipItem(warrior=warrior, item=new_item, slot="weapon"))

    assert result.previous_holder is None
    # Read back off fresh rows: assigning the slot above cached this warrior as the item's wearer
    warrior.refresh_from_db()
    assert (warrior.weapon, Item.objects.get(id=held_item.id).worn_by) == (new_item, None)


@pytest.mark.django_db
def test_handle_equip_item_empties_the_slot():
    warrior = WarriorFactory()
    item = ItemFactory(savegame=warrior.savegame, owner=warrior.faction)
    warrior.weapon = item
    warrior.save()

    result = handle_equip_item(context=EquipItem(warrior=warrior, item=None, slot="weapon"))

    assert result == ItemEquipped(warrior=warrior, item=None, slot="weapon", previous_holder=None, displaced_item=item)
    warrior.refresh_from_db()
    assert warrior.weapon is None


@pytest.mark.django_db
def test_handle_equip_item_keeps_the_item_a_warrior_already_holds():
    """
    Saving the slot on the item already in it. The same man on both ends of the move is the one case
    where the swap would write his own item back onto him after emptying the slot.
    """
    warrior = WarriorFactory()
    item = ItemFactory(savegame=warrior.savegame, owner=warrior.faction)
    warrior.weapon = item
    warrior.save()

    result = handle_equip_item(context=EquipItem(warrior=warrior, item=item, slot="weapon"))

    assert result.previous_holder is None
    warrior.refresh_from_db()
    assert warrior.weapon == item


@pytest.mark.django_db
def test_handle_equip_item_leaves_the_other_slot_alone():
    warrior = WarriorFactory()
    armor = ItemFactory(
        savegame=warrior.savegame,
        owner=warrior.faction,
        type=ItemTypeFactory(function=ItemType.FunctionChoices.FUNCTION_ARMOR),
    )
    warrior.armor = armor
    warrior.save()
    weapon = ItemFactory(savegame=warrior.savegame, owner=warrior.faction)

    handle_equip_item(context=EquipItem(warrior=warrior, item=weapon, slot="weapon"))

    warrior.refresh_from_db()
    assert warrior.armor == armor


@pytest.mark.django_db
def test_handle_create_item_puts_an_owned_item_in_its_owners_stores():
    faction = FactionFactory()
    ItemTypeFactory(function=ItemType.FunctionChoices.FUNCTION_WEAPON, tier=ItemType.TierChoices.TIER_RUSTIC)

    result = handle_create_item(
        context=CreateItem(
            owner=faction,
            faction=faction,
            generator_class=FyrdItemGenerator,
            item_function=ItemType.FunctionChoices.FUNCTION_WEAPON,
            month=1,
        )
    )

    assert result == ItemCreated(owner=faction, faction=faction, item=result.item, month=1)
    assert Item.objects.get(pk=result.item.pk).owner == faction
