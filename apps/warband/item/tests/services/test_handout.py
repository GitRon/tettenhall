import pytest

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.item.models.item_type import ItemType
from apps.warband.item.services.handout import (
    annotate_held_gear_values,
    count_stored_upgrades,
    get_handout_note,
    plan_gear_handout,
    rank_for_slot,
)
from apps.warband.item.tests.factories.item import ItemFactory
from apps.warband.item.tests.factories.item_type import ItemTypeFactory
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_annotate_held_gear_values_reads_a_filled_slot_off_the_item():
    warrior = WarriorFactory()
    warrior.weapon = ItemFactory(
        savegame=warrior.savegame,
        owner=warrior.faction,
        type=ItemTypeFactory(base_value="2d6"),
    )
    warrior.save()

    result = annotate_held_gear_values(roster=[warrior])

    assert result[0].held_gear_values["weapon"] == 7


@pytest.mark.django_db
def test_annotate_held_gear_values_reads_an_empty_slot_off_the_fallback():
    """
    A bare-handed man still throws the fallback's dice, so an empty slot is worth what the fight says
    it is worth rather than nothing - which would call every empty slot the same and rank none of
    them against each other.
    """
    warrior = WarriorFactory()

    result = annotate_held_gear_values(roster=[warrior])

    assert result[0].held_gear_values == {"weapon": 2, "armor": 1.5}


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


@pytest.mark.django_db
def test_count_stored_upgrades_counts_an_item_better_than_what_a_man_holds():
    warrior = WarriorFactory()
    warrior.weapon = ItemFactory(
        savegame=warrior.savegame, owner=warrior.faction, type=ItemTypeFactory(base_value="1d4")
    )
    warrior.save()
    ItemFactory(savegame=warrior.savegame, owner=warrior.faction, type=ItemTypeFactory(base_value="2d6"))

    result = count_stored_upgrades(faction=warrior.faction)

    assert result == 1


@pytest.mark.django_db
def test_count_stored_upgrades_leaves_out_a_spare_nobody_would_gain_from():
    """
    A shield kept on purpose, no better than what every man already carries, is not waiting on the
    player - counting it would put the same row in front of him every month.
    """
    warrior = WarriorFactory()
    warrior.weapon = ItemFactory(
        savegame=warrior.savegame, owner=warrior.faction, type=ItemTypeFactory(base_value="2d6")
    )
    warrior.save()
    ItemFactory(savegame=warrior.savegame, owner=warrior.faction, type=ItemTypeFactory(base_value="2d6"))

    result = count_stored_upgrades(faction=warrior.faction)

    assert result == 0


@pytest.mark.django_db
def test_count_stored_upgrades_is_nil_with_nobody_to_hand_anything_to():
    faction = FactionFactory()
    ItemFactory(savegame=faction.savegame, owner=faction, type=ItemTypeFactory(base_value="2d6"))

    result = count_stored_upgrades(faction=faction)

    assert result == 0


def _armour_type(*, base_value: str) -> ItemType:
    return ItemTypeFactory(function=ItemType.FunctionChoices.FUNCTION_ARMOR, base_value=base_value)


@pytest.mark.django_db
def test_rank_for_slot_puts_the_leader_before_a_man_of_higher_level():
    faction = FactionFactory()
    veteran = WarriorFactory(faction=faction, experience=Warrior.XP_LEVEL_BASE * 4)
    leader = WarriorFactory(faction=faction, experience=0)

    result = rank_for_slot(roster=[veteran, leader], leader_id=leader.id, slot="weapon")

    assert result == [leader, veteran]


@pytest.mark.django_db
def test_rank_for_slot_breaks_a_level_tie_on_strength_for_a_weapon():
    weak = WarriorFactory(strength=8)
    strong = WarriorFactory(faction=weak.faction, strength=14)

    result = rank_for_slot(roster=[weak, strong], leader_id=None, slot="weapon")

    assert result == [strong, weak]


@pytest.mark.django_db
def test_rank_for_slot_breaks_a_level_tie_on_health_for_armour():
    """The man with the most to lose to a blow, where a weapon goes to the one it does most for."""
    frail = WarriorFactory(max_health=12, current_health=12, strength=14)
    sturdy = WarriorFactory(faction=frail.faction, max_health=30, current_health=30, strength=8)

    result = rank_for_slot(roster=[frail, sturdy], leader_id=None, slot="armor")

    assert result == [sturdy, frail]


@pytest.mark.django_db
def test_plan_gear_handout_gives_the_leader_the_best_of_each_slot_first():
    faction = FactionFactory()
    veteran = WarriorFactory(faction=faction, experience=Warrior.XP_LEVEL_BASE * 4)
    leader = WarriorFactory(faction=faction)
    faction.leader = leader
    faction.save()
    sword = ItemFactory(savegame=faction.savegame, owner=faction, type=ItemTypeFactory(base_value="2d6"))
    mail = ItemFactory(savegame=faction.savegame, owner=faction, type=_armour_type(base_value="2d6"))

    result = plan_gear_handout(faction=faction)

    assert result == [(leader, sword, "weapon"), (leader, mail, "armor")]
    assert veteran not in [warrior for warrior, _item, _slot in result]


@pytest.mark.django_db
def test_plan_gear_handout_leaves_an_item_that_improves_nobody_in_the_stores():
    warrior = WarriorFactory()
    warrior.weapon = ItemFactory(
        savegame=warrior.savegame, owner=warrior.faction, type=ItemTypeFactory(base_value="2d6")
    )
    warrior.save()
    ItemFactory(savegame=warrior.savegame, owner=warrior.faction, type=ItemTypeFactory(base_value="1d6"))

    result = plan_gear_handout(faction=warrior.faction)

    assert result == []


@pytest.mark.django_db
def test_plan_gear_handout_passes_a_displaced_item_on_to_the_next_man_it_improves():
    """The mercenary's old sword ends up on the levy rather than back in the stores."""
    faction = FactionFactory()
    mercenary = WarriorFactory(faction=faction, experience=Warrior.XP_LEVEL_BASE * 4)
    levy = WarriorFactory(faction=faction)
    old_sword = ItemFactory(savegame=faction.savegame, owner=faction, type=ItemTypeFactory(base_value="1d6"))
    mercenary.weapon = old_sword
    mercenary.save()
    new_sword = ItemFactory(savegame=faction.savegame, owner=faction, type=ItemTypeFactory(base_value="2d6"))

    result = plan_gear_handout(faction=faction)

    assert result == [(mercenary, new_sword, "weapon"), (levy, old_sword, "weapon")]


@pytest.mark.django_db
def test_plan_gear_handout_takes_a_better_item_off_a_lower_man_in_exchange():
    """
    The leader takes the levy's sword and the levy gets the leader's in return, which is then the best
    he can have - so it is one equip, and the swap in "handle_equip_item" does the rest.
    """
    faction = FactionFactory()
    leader = WarriorFactory(faction=faction)
    levy = WarriorFactory(faction=faction)
    faction.leader = leader
    faction.save()
    leader.weapon = ItemFactory(savegame=faction.savegame, owner=faction, type=ItemTypeFactory(base_value="1d4"))
    leader.save()
    good_sword = ItemFactory(savegame=faction.savegame, owner=faction, type=ItemTypeFactory(base_value="2d6"))
    levy.weapon = good_sword
    levy.save()

    result = plan_gear_handout(faction=faction)

    assert result == [(leader, good_sword, "weapon")]


@pytest.mark.django_db
def test_plan_gear_handout_skips_a_man_in_an_open_fight_and_what_he_holds():
    faction = FactionFactory()
    fighting = WarriorFactory(faction=faction, experience=Warrior.XP_LEVEL_BASE * 4)
    fighting.weapon = ItemFactory(savegame=faction.savegame, owner=faction, type=ItemTypeFactory(base_value="2d6"))
    fighting.save()
    WarriorFactory(faction=faction)
    skirmish = SkirmishFactory(attacking_faction=faction, victorious_faction=None)
    skirmish.attacking_warriors.add(fighting)

    result = plan_gear_handout(faction=faction)

    assert result == []


@pytest.mark.django_db
def test_plan_gear_handout_moves_nothing_for_one_man_and_empty_stores():
    warrior = WarriorFactory()
    warrior.weapon = ItemFactory(
        savegame=warrior.savegame, owner=warrior.faction, type=ItemTypeFactory(base_value="1d4")
    )
    warrior.save()

    result = plan_gear_handout(faction=warrior.faction)

    assert result == []
