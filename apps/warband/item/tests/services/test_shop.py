import pytest

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.item.services.shop import annotate_stored_copy_counts
from apps.warband.item.tests.factories.item import ItemFactory
from apps.warband.item.tests.factories.item_type import ItemTypeFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_annotate_stored_copy_counts_counts_the_unused_items_of_the_same_type():
    """
    Matched on the type, so a worn seax lying in the stores answers for the fine one on the stall -
    they are the same weapon in the hand.
    """
    faction = FactionFactory()
    seax = ItemTypeFactory(name="Seax")
    ItemFactory(savegame=faction.savegame, owner=faction, type=seax)
    ItemFactory(savegame=faction.savegame, owner=faction, type=ItemTypeFactory())
    on_the_stall = ItemFactory(savegame=faction.savegame, type=seax)

    items, _ = annotate_stored_copy_counts(item_list=[on_the_stall], faction=faction)

    assert items[0].stored_copy_count == 1


@pytest.mark.django_db
def test_annotate_stored_copy_counts_leaves_out_what_a_man_is_carrying():
    faction = FactionFactory()
    warrior = WarriorFactory(faction=faction, savegame=faction.savegame)
    warrior.weapon = ItemFactory(savegame=faction.savegame, owner=faction)
    warrior.save()
    ItemFactory(savegame=faction.savegame, owner=faction)

    _, stored_item_count = annotate_stored_copy_counts(item_list=[], faction=faction)

    assert stored_item_count == 1
