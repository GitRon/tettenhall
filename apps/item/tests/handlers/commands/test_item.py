import pytest

from apps.faction.tests.factories.faction import FactionFactory
from apps.item.handlers.commands.item import handle_change_ownership
from apps.item.messages.commands.item import ChangeOwnership
from apps.item.messages.events.item import OwnershipChanged
from apps.item.tests.factories.item import ItemFactory
from apps.skirmish.tests.factories.warrior import WarriorFactory


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
