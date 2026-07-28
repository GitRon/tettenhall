import pytest

from apps.item.models.item_type import ItemType
from apps.item.tests.factories.item import ItemFactory
from apps.item.tests.factories.item_type import ItemTypeFactory
from apps.skirmish.handlers.commands.item import handle_warrior_drops_loot
from apps.skirmish.messages.commands.item import WarriorDropsLoot
from apps.skirmish.messages.events.item import ItemDroppedAsLoot
from apps.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_handle_warrior_drops_loot_drops_weapon_and_armor():
    skirmish = SkirmishFactory()
    weapon = ItemFactory(savegame=skirmish.player_faction.savegame)
    armor = ItemFactory(
        savegame=skirmish.player_faction.savegame,
        type=ItemTypeFactory(function=ItemType.FunctionChoices.FUNCTION_ARMOR),
    )
    warrior = WarriorFactory(faction=skirmish.non_player_faction, weapon=weapon, armor=armor)

    result = handle_warrior_drops_loot(
        context=WarriorDropsLoot(skirmish=skirmish, warrior=warrior, new_owner=skirmish.player_faction)
    )

    assert result == [
        ItemDroppedAsLoot(
            skirmish=skirmish,
            warrior=warrior,
            item=weapon,
            item_name=weapon.display_name,
            new_owner=skirmish.player_faction,
        ),
        ItemDroppedAsLoot(
            skirmish=skirmish,
            warrior=warrior,
            item=armor,
            item_name=armor.display_name,
            new_owner=skirmish.player_faction,
        ),
    ]


@pytest.mark.django_db
def test_handle_warrior_drops_loot_drops_nothing_for_an_unequipped_warrior():
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.non_player_faction, weapon=None, armor=None)

    result = handle_warrior_drops_loot(
        context=WarriorDropsLoot(skirmish=skirmish, warrior=warrior, new_owner=skirmish.player_faction)
    )

    assert result == []
