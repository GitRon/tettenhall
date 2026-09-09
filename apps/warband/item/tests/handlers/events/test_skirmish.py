from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.item.handlers.events.skirmish import handle_looted_item_changes_ownership
from apps.warband.item.messages.commands.item import ChangeOwnership
from apps.warband.item.tests.factories.item import ItemFactory
from apps.warband.skirmish.messages.events.item import ItemDroppedAsLoot
from apps.warband.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory


def test_handle_looted_item_changes_ownership_maps_to_a_command():
    warrior = WarriorFactory.build()
    item = ItemFactory.build()
    new_owner = FactionFactory.build()

    result = handle_looted_item_changes_ownership(
        context=ItemDroppedAsLoot(
            skirmish=SkirmishFactory.build(),
            warrior=warrior,
            item=item,
            item_name="Superior Battle axe",
            new_owner=new_owner,
        )
    )

    assert result == ChangeOwnership(previous_owner=warrior, item=item, new_owner=new_owner)
