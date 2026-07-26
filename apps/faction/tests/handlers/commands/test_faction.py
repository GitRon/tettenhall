from unittest import mock

import pytest

from apps.faction.handlers.commands.faction import (
    handle_create_new_faction,
    handle_determine_injured_warriors,
    handle_replenish_fyrd_reserve,
    handle_restock_shop_items,
)
from apps.faction.messages.commands.faction import (
    CreateNewFaction,
    DetermineInjuredWarriors,
    ReplenishFyrdReserve,
    RestockTownShopItems,
)
from apps.faction.messages.events.faction import (
    FactionFyrdReserveReplenished,
    NewFactionCreated,
    RequestNewItemForTownShop,
)
from apps.faction.models.faction import Faction
from apps.faction.tests.factories.culture import CultureFactory
from apps.faction.tests.factories.faction import FactionFactory
from apps.item.models import ItemType
from apps.item.services.generators.item.mercenary import MercenaryItemGenerator
from apps.item.tests.factories.item import ItemFactory
from apps.savegame.tests.factories.savegame import SavegameFactory
from apps.skirmish.models.warrior import Warrior
from apps.skirmish.tests.factories.warrior import WarriorFactory
from apps.warrior.messages.commands.warrior import HealInjuredWarrior


@pytest.mark.django_db
def test_handle_create_new_faction_for_player_faction():
    savegame = SavegameFactory(current_month=5)
    culture = CultureFactory()

    with mock.patch("apps.faction.handlers.commands.faction.random.randint", return_value=4):
        result = handle_create_new_faction(
            context=CreateNewFaction(name="Wessex", culture_id=culture.id, savegame=savegame, is_player_faction=True)
        )

    assert result == NewFactionCreated(faction=Faction.objects.get(name="Wessex"), current_month=5)
    savegame.refresh_from_db()
    assert savegame.player_faction == result.faction


@pytest.mark.django_db
def test_handle_create_new_faction_for_non_player_faction():
    savegame = SavegameFactory(current_month=5)
    culture = CultureFactory()

    with mock.patch("apps.faction.handlers.commands.faction.random.randint", return_value=4):
        result = handle_create_new_faction(
            context=CreateNewFaction(name="Mercia", culture_id=culture.id, savegame=savegame, is_player_faction=False)
        )

    assert result.faction.fyrd_reserve == 4
    savegame.refresh_from_db()
    assert savegame.player_faction is None


@pytest.mark.django_db
def test_handle_restock_shop_items_requests_weapons():
    faction = FactionFactory()

    with (
        mock.patch("apps.faction.handlers.commands.faction.random.randrange", return_value=4),
        mock.patch("apps.faction.handlers.commands.faction.random.getrandbits", return_value=1),
    ):
        result = handle_restock_shop_items(context=RestockTownShopItems(faction=faction, month=3))

    expected_message = RequestNewItemForTownShop(
        faction=faction,
        generator_class=MercenaryItemGenerator,
        item_function=ItemType.FunctionChoices.FUNCTION_WEAPON,
        month=3,
    )
    assert result == [expected_message] * 4


@pytest.mark.django_db
def test_handle_restock_shop_items_requests_armor():
    faction = FactionFactory()

    with (
        mock.patch("apps.faction.handlers.commands.faction.random.randrange", return_value=4),
        mock.patch("apps.faction.handlers.commands.faction.random.getrandbits", return_value=0),
    ):
        result = handle_restock_shop_items(context=RestockTownShopItems(faction=faction, month=3))

    expected_message = RequestNewItemForTownShop(
        faction=faction,
        generator_class=MercenaryItemGenerator,
        item_function=ItemType.FunctionChoices.FUNCTION_ARMOR,
        month=3,
    )
    assert result == [expected_message] * 4


@pytest.mark.django_db
def test_handle_restock_shop_items_removes_previous_stock():
    faction = FactionFactory()
    faction.available_items.add(ItemFactory())

    with (
        mock.patch("apps.faction.handlers.commands.faction.random.randrange", return_value=4),
        mock.patch("apps.faction.handlers.commands.faction.random.getrandbits", return_value=1),
    ):
        handle_restock_shop_items(context=RestockTownShopItems(faction=faction, month=3))

    assert faction.available_items.count() == 0


@pytest.mark.django_db
def test_handle_replenish_fyrd_reserve_with_new_recruitees():
    faction = FactionFactory(fyrd_reserve=3)

    with mock.patch("apps.faction.handlers.commands.faction.random.randrange", return_value=2):
        result = handle_replenish_fyrd_reserve(context=ReplenishFyrdReserve(faction=faction, month=3))

    assert result == FactionFyrdReserveReplenished(faction=faction, new_recruitees=2, month=3)
    faction.refresh_from_db()
    assert faction.fyrd_reserve == 5


@pytest.mark.django_db
def test_handle_replenish_fyrd_reserve_without_new_recruitees():
    faction = FactionFactory(fyrd_reserve=3)

    with mock.patch("apps.faction.handlers.commands.faction.random.randrange", return_value=0):
        result = handle_replenish_fyrd_reserve(context=ReplenishFyrdReserve(faction=faction, month=3))

    assert result is None
    faction.refresh_from_db()
    assert faction.fyrd_reserve == 3


@pytest.mark.django_db
def test_handle_determine_injured_warriors_with_injured_warrior():
    injured_warrior = WarriorFactory(current_health=5, max_health=20)

    result = handle_determine_injured_warriors(
        context=DetermineInjuredWarriors(faction=injured_warrior.faction, month=3)
    )

    assert result == [HealInjuredWarrior(warrior=injured_warrior, month=3)]


@pytest.mark.django_db
def test_handle_determine_injured_warriors_without_injured_warriors():
    healthy_warrior = WarriorFactory(current_health=20, max_health=20)

    result = handle_determine_injured_warriors(
        context=DetermineInjuredWarriors(faction=healthy_warrior.faction, month=3)
    )

    assert result == []


@pytest.mark.django_db
def test_handle_determine_injured_warriors_ignores_dead_warriors():
    dead_warrior = WarriorFactory(current_health=0, max_health=20, condition=Warrior.ConditionChoices.CONDITION_DEAD)

    result = handle_determine_injured_warriors(context=DetermineInjuredWarriors(faction=dead_warrior.faction, month=3))

    assert result == []
