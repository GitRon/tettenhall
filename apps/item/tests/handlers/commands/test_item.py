import pytest

from apps.faction.tests.factories.faction import FactionFactory
from apps.item.handlers.commands.item import handle_change_ownership, handle_sell_item
from apps.item.messages.commands.item import ChangeOwnership, SellItem
from apps.item.messages.events.item import ItemSold, OwnershipChanged
from apps.item.tests.factories.item import ItemFactory
from apps.skirmish.tests.factories.warrior import WarriorFactory


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
