from unittest import mock

import pytest

from apps.faction.handlers.commands.warrior import handle_draft_warrior_from_fyrd, handle_restock_pub_mercenaries
from apps.faction.messages.commands.warrior import DraftWarriorFromFyrd, RestockTownMercenaries
from apps.faction.messages.events.warrior import RequestWarriorForPub, WarriorRecruited
from apps.faction.tests.factories.faction import FactionFactory
from apps.item.models import ItemType
from apps.item.tests.factories.item_type import ItemTypeFactory
from apps.skirmish.models import Warrior
from apps.skirmish.tests.factories.warrior import WarriorFactory
from apps.warrior.services.generators.warrior.mercenary import MercenaryWarriorGenerator


@pytest.mark.django_db
def test_handle_restock_pub_mercenaries_requests_one_warrior_per_drawn_slot():
    faction = FactionFactory()

    with mock.patch("apps.faction.handlers.commands.warrior.random.randrange", return_value=2):
        result = handle_restock_pub_mercenaries(context=RestockTownMercenaries(faction=faction, month=3))

    expected_message = RequestWarriorForPub(
        savegame=faction.savegame,
        faction=None,
        culture=faction.culture,
        generator_class=MercenaryWarriorGenerator,
        month=3,
    )
    assert result == [expected_message] * 2


@pytest.mark.django_db
def test_handle_restock_pub_mercenaries_removes_previous_stock():
    faction = FactionFactory()
    faction.available_mercenaries.add(WarriorFactory(faction=faction))

    with mock.patch("apps.faction.handlers.commands.warrior.random.randrange", return_value=2):
        handle_restock_pub_mercenaries(context=RestockTownMercenaries(faction=faction, month=3))

    assert faction.available_mercenaries.count() == 0


@pytest.mark.django_db
def test_handle_draft_warrior_from_fyrd_with_filled_reserve():
    faction = FactionFactory(fyrd_reserve=3)
    # FyrdItemGenerator hard-codes the weapon names it draws from, so the name has to match
    ItemTypeFactory(name="Spear", function=ItemType.FunctionChoices.FUNCTION_WEAPON)
    ItemTypeFactory(name="Gambeson", function=ItemType.FunctionChoices.FUNCTION_ARMOR)

    result = handle_draft_warrior_from_fyrd(context=DraftWarriorFromFyrd(faction=faction, month=3))

    assert result == WarriorRecruited(
        faction=faction, warrior=Warrior.objects.get(faction=faction), recruitment_price=0, month=3
    )
    faction.refresh_from_db()
    assert faction.fyrd_reserve == 2


@pytest.mark.django_db
def test_handle_draft_warrior_from_fyrd_with_empty_reserve():
    faction = FactionFactory(fyrd_reserve=0)

    result = handle_draft_warrior_from_fyrd(context=DraftWarriorFromFyrd(faction=faction, month=3))

    assert result is None
    assert Warrior.objects.filter(faction=faction).exists() is False
