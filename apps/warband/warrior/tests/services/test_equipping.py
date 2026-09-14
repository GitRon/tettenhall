import pytest

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.item.tests.factories.item import ItemFactory
from apps.warband.quest.tests.factories.quest_contract import QuestContractFactory
from apps.warband.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.warrior.services.equipping import (
    HOLDER_REFUSAL,
    WEARER_REFUSAL,
    get_equip_refusal,
    get_unequip_refusal,
    get_warriors_in_an_open_fight,
)


@pytest.mark.django_db
def test_get_warriors_in_an_open_fight_finds_the_man_on_the_roster():
    faction = FactionFactory()
    fighting = WarriorFactory(faction=faction)
    free = WarriorFactory(faction=faction)
    skirmish = SkirmishFactory(attacking_faction=faction, victorious_faction=None)
    skirmish.attacking_warriors.add(fighting)

    result = get_warriors_in_an_open_fight(warrior_list=[fighting, free])

    assert result == {fighting.id}


@pytest.mark.django_db
def test_get_equip_refusal_lets_a_free_man_be_re_armed():
    faction = FactionFactory()
    warrior = WarriorFactory(faction=faction)
    item = ItemFactory(savegame=faction.savegame, owner=faction)

    result = get_equip_refusal(warrior=warrior, item=item)

    assert result is None


@pytest.mark.django_db
def test_get_equip_refusal_refuses_a_man_standing_in_an_open_fight():
    faction = FactionFactory()
    warrior = WarriorFactory(faction=faction)
    skirmish = SkirmishFactory(attacking_faction=faction, victorious_faction=None)
    skirmish.attacking_warriors.add(warrior)

    result = get_equip_refusal(warrior=warrior, item=None)

    assert result == WEARER_REFUSAL


@pytest.mark.django_db
def test_get_equip_refusal_lets_a_man_whose_fight_is_settled_be_re_armed():
    """
    The rule is the open fight and not the month: a settled skirmish has no blow left to roll off the
    slot, so the gear is the player's to move again the moment it is decided.
    """
    faction = FactionFactory()
    warrior = WarriorFactory(faction=faction)
    skirmish = SkirmishFactory(attacking_faction=faction, victorious_faction=faction, month=3)
    skirmish.attacking_warriors.add(warrior)

    result = get_equip_refusal(warrior=warrior, item=None)

    assert result is None


@pytest.mark.django_db
def test_get_equip_refusal_lets_a_man_sworn_to_a_quest_be_re_armed():
    """
    Deliberately narrower than "get_dismissal_refusals", which refuses him: arming before you march
    is the decision the gear economy is built on, and a quest contract rolls no dice off the slot.
    """
    faction = FactionFactory()
    warrior = WarriorFactory(faction=faction)
    quest_contract = QuestContractFactory(faction=faction, accepted_in_month=3)
    quest_contract.assigned_warriors.add(warrior)

    result = get_equip_refusal(warrior=warrior, item=None)

    assert result is None


@pytest.mark.django_db
def test_get_equip_refusal_refuses_the_far_end_of_a_swap():
    """
    The receiver is safely at home and the sword is on a man in the line, which is the whole exploit
    reached from the other end.
    """
    faction = FactionFactory()
    receiver = WarriorFactory(faction=faction)
    holder = WarriorFactory(faction=faction)
    item = ItemFactory(savegame=faction.savegame, owner=faction)
    holder.weapon = item
    holder.save()
    skirmish = SkirmishFactory(attacking_faction=faction, victorious_faction=None)
    skirmish.attacking_warriors.add(holder)

    result = get_equip_refusal(warrior=receiver, item=item)

    assert result == HOLDER_REFUSAL.format(name=holder.display_name)


@pytest.mark.django_db
def test_get_equip_refusal_names_the_wearer_before_the_holder():
    """
    Nothing the player picks makes his own man editable, while a different item is one click away -
    the order "get_building_upgrade_refusal" puts its own guards in.
    """
    faction = FactionFactory()
    receiver = WarriorFactory(faction=faction)
    holder = WarriorFactory(faction=faction)
    item = ItemFactory(savegame=faction.savegame, owner=faction)
    holder.weapon = item
    holder.save()
    skirmish = SkirmishFactory(attacking_faction=faction, victorious_faction=None)
    skirmish.attacking_warriors.add(receiver, holder)

    result = get_equip_refusal(warrior=receiver, item=item)

    assert result == WEARER_REFUSAL


@pytest.mark.django_db
def test_get_unequip_refusal_lets_an_unworn_item_go():
    faction = FactionFactory()
    item = ItemFactory(savegame=faction.savegame, owner=faction)

    result = get_unequip_refusal(item=item)

    assert result is None


@pytest.mark.django_db
def test_get_unequip_refusal_lets_the_gear_of_a_free_man_go():
    faction = FactionFactory()
    holder = WarriorFactory(faction=faction)
    item = ItemFactory(savegame=faction.savegame, owner=faction)
    holder.weapon = item
    holder.save()

    result = get_unequip_refusal(item=item)

    assert result is None


@pytest.mark.django_db
def test_get_unequip_refusal_keeps_the_gear_on_a_man_in_an_open_fight():
    faction = FactionFactory()
    holder = WarriorFactory(faction=faction)
    item = ItemFactory(savegame=faction.savegame, owner=faction)
    holder.weapon = item
    holder.save()
    skirmish = SkirmishFactory(attacking_faction=faction, victorious_faction=None)
    skirmish.defending_warriors.add(holder)

    result = get_unequip_refusal(item=item)

    assert result == HOLDER_REFUSAL.format(name=holder.display_name)
