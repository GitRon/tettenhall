import pytest

from apps.warband.item.models.item_type import ItemType
from apps.warband.item.services.handout import get_handout_note
from apps.warband.item.tests.factories.item import ItemFactory
from apps.warband.item.tests.factories.item_type import ItemTypeFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_get_handout_note_names_the_exchange_when_both_slots_are_full():
    receiver = WarriorFactory(name="Eadric")
    holder = WarriorFactory(faction=receiver.faction, name="Wulfric")
    receiver.weapon = ItemFactory(
        savegame=receiver.savegame,
        owner=receiver.faction,
        type=ItemTypeFactory(name="Spear"),
    )
    receiver.save()
    holder.weapon = ItemFactory(savegame=receiver.savegame, owner=receiver.faction)
    holder.save()

    note = get_handout_note(warrior=receiver, item=holder.weapon, slot="weapon")

    assert note == "Taken off Wulfric, who takes the Traditional Spear in exchange."


@pytest.mark.django_db
def test_get_handout_note_says_the_previous_holder_is_left_with_nothing():
    receiver = WarriorFactory()
    holder = WarriorFactory(faction=receiver.faction, name="Wulfric")
    holder.armor = ItemFactory(
        savegame=receiver.savegame,
        owner=receiver.faction,
        type=ItemTypeFactory(function=ItemType.FunctionChoices.FUNCTION_ARMOR),
    )
    holder.save()

    note = get_handout_note(warrior=receiver, item=holder.armor, slot="armor")

    assert note == "Taken off Wulfric, who now carries no armour."


@pytest.mark.django_db
def test_get_handout_note_says_where_a_displaced_item_went():
    warrior = WarriorFactory(name="Eadric")
    warrior.weapon = ItemFactory(
        savegame=warrior.savegame,
        owner=warrior.faction,
        type=ItemTypeFactory(name="Spear"),
    )
    warrior.save()
    new_item = ItemFactory(savegame=warrior.savegame, owner=warrior.faction)

    note = get_handout_note(warrior=warrior, item=new_item, slot="weapon")

    assert note == "Eadric puts the Traditional Spear back in the stash."


@pytest.mark.django_db
def test_get_handout_note_stays_quiet_when_nothing_happened_offscreen():
    """
    An empty slot filled from the stash: the cell the player is looking at is the whole of it, and a
    toast repeating what he can see is noise.
    """
    warrior = WarriorFactory()
    item = ItemFactory(savegame=warrior.savegame, owner=warrior.faction)

    assert get_handout_note(warrior=warrior, item=item, slot="weapon") is None


@pytest.mark.django_db
def test_get_handout_note_says_where_an_emptied_slot_sends_its_item():
    warrior = WarriorFactory(name="Eadric")
    warrior.weapon = ItemFactory(
        savegame=warrior.savegame,
        owner=warrior.faction,
        type=ItemTypeFactory(name="Spear"),
    )
    warrior.save()

    note = get_handout_note(warrior=warrior, item=None, slot="weapon")

    assert note == "Eadric puts the Traditional Spear back in the stash."


@pytest.mark.django_db
def test_get_handout_note_stays_quiet_when_the_man_keeps_what_he_has():
    """
    The same man on both ends is the player saving the slot unchanged. Reading him as the previous
    holder would announce that he had taken his own sword off himself.
    """
    warrior = WarriorFactory()
    warrior.weapon = ItemFactory(savegame=warrior.savegame, owner=warrior.faction)
    warrior.save()

    assert get_handout_note(warrior=warrior, item=warrior.weapon, slot="weapon") is None
