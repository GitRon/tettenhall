from apps.warband.faction.messages.events.faction import NewFactionCreated
from apps.warband.faction.messages.events.item import GearHandoutApproved, RequestNewItemForTownShop
from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.item.handlers.events.faction import (
    STARTING_GEAR_QUALITY_BONUS,
    handle_equip_item_for_approved_gear_handout,
    handle_request_new_item_for_town_shop,
    handle_stock_starting_gear_for_player_faction,
)
from apps.warband.item.messages.commands.item import CreateItem, EquipItem
from apps.warband.item.models.item_type import ItemType
from apps.warband.item.services.generators.item.fyrd import FyrdItemGenerator
from apps.warband.item.services.generators.item.mercenary import MercenaryItemGenerator
from apps.warband.item.tests.factories.item import ItemFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory


def test_handle_request_new_item_for_town_shop_maps_to_command():
    """
    Pure mapping, so an unsaved faction is enough.

    The handler must not reach through "faction.savegame" here, which is a query whenever that
    relation is not already cached - and strict mode forbids those in an event handler. What keeps
    it that way is not this test but CreateItem having no savegame field at all: its handler derives
    one from "faction.savegame_id", so there is nothing to pass.
    """
    faction = FactionFactory.build()

    result = handle_request_new_item_for_town_shop(
        context=RequestNewItemForTownShop(
            faction=faction,
            generator_class=MercenaryItemGenerator,
            item_function=ItemType.FunctionChoices.FUNCTION_WEAPON,
            month=3,
            quality_bonus=2,
            item_tiers=frozenset({ItemType.TierChoices.TIER_FINE}),
        )
    )

    assert result == CreateItem(
        owner=None,
        faction=faction,
        generator_class=MercenaryItemGenerator,
        item_function=ItemType.FunctionChoices.FUNCTION_WEAPON,
        month=3,
        quality_bonus=2,
        item_tiers=frozenset({ItemType.TierChoices.TIER_FINE}),
    )


def test_handle_stock_starting_gear_for_player_faction_hands_the_player_a_poor_weapon_and_armour():
    faction = FactionFactory.build()

    result = handle_stock_starting_gear_for_player_faction(
        context=NewFactionCreated(faction=faction, current_month=1, is_player=True)
    )

    assert result == [
        CreateItem(
            owner=faction,
            faction=faction,
            generator_class=FyrdItemGenerator,
            item_function=ItemType.FunctionChoices.FUNCTION_WEAPON,
            month=1,
            quality_bonus=STARTING_GEAR_QUALITY_BONUS,
        ),
        CreateItem(
            owner=faction,
            faction=faction,
            generator_class=FyrdItemGenerator,
            item_function=ItemType.FunctionChoices.FUNCTION_ARMOR,
            month=1,
            quality_bonus=STARTING_GEAR_QUALITY_BONUS,
        ),
    ]


def test_handle_stock_starting_gear_for_player_faction_leaves_a_rival_empty_handed():
    result = handle_stock_starting_gear_for_player_faction(
        context=NewFactionCreated(faction=FactionFactory.build(), current_month=1, is_player=False)
    )

    assert result is None


def test_handle_equip_item_for_approved_gear_handout_maps_to_command():
    """
    Pure mapping: handle_hand_out_faction_gear weighed the whole decision, which is what lets a rival arm
    its men through the same command the player's own handout dispatches.
    """
    warrior = WarriorFactory.build()
    sword = ItemFactory.build()

    result = handle_equip_item_for_approved_gear_handout(
        context=GearHandoutApproved(faction=warrior.faction, warrior=warrior, item=sword, slot="weapon")
    )

    assert result == EquipItem(warrior=warrior, item=sword, slot="weapon")
