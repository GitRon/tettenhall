import pytest

from apps.warband.faction.models.faction import Faction
from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.item.models.item import Item
from apps.warband.item.services.upgrade import (
    ALREADY_UPGRADED_THIS_MONTH_REFUSAL,
    BEYOND_THE_FORGE_REFUSAL,
    NO_WEAPONSMITH_REFUSAL,
    NOT_YOURS_REFUSAL,
    SUPERIOR_REFUSAL,
    UNAFFORDABLE_REFUSAL,
    UNWORKABLE_REFUSAL,
    ItemUpgrade,
    get_item_upgrade,
    get_item_upgrade_offer,
    get_item_upgrade_refusal,
)
from apps.warband.item.tests.factories.item import ItemFactory
from apps.warband.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.town.models import Town
from apps.warband.warrior.services.equipping import HOLDER_REFUSAL


def _faction_with_weaponsmith(*, level: int = Town.WeaponsmithChoices.WEAPONSMITH_LARGE) -> Faction:
    return FactionFactory(town__weaponsmith=level)


def _rusty_item(*, faction: Faction, **kwargs) -> Item:
    # A 1d6 at +0 averages 3.5 and is priced at 70; the step to +2 averages 5.5 and is priced at 110
    return ItemFactory(
        savegame=faction.savegame,
        owner=faction,
        condition=Item.ConditionChoices.CONDITION_RUSTY,
        modifier=0,
        price=70,
        **kwargs,
    )


@pytest.mark.django_db
def test_get_item_upgrade_raises_condition_and_modifier_and_prices_the_difference():
    faction = FactionFactory()
    item = _rusty_item(faction=faction)

    result = get_item_upgrade(item=item)

    assert result == ItemUpgrade(condition=Item.ConditionChoices.CONDITION_CHEAP, modifier=2, price=110, costs=40)


@pytest.mark.django_db
def test_get_item_upgrade_never_costs_nothing():
    """
    An item priced above what its dice are worth - a list price from before a balance change, say -
    would otherwise be reworked for free or for a refund.
    """
    faction = FactionFactory()
    item = _rusty_item(faction=faction)
    Item.objects.filter(pk=item.pk).update(price=500)
    item.refresh_from_db()

    result = get_item_upgrade(item=item)

    assert result.costs == 1


@pytest.mark.django_db
def test_get_item_upgrade_for_a_superior_item_is_none():
    item = ItemFactory(condition=Item.ConditionChoices.CONDITION_SUPERIOR)

    result = get_item_upgrade(item=item)

    assert result is None


@pytest.mark.django_db
def test_get_item_upgrade_refusal_lets_a_rework_through():
    faction = _faction_with_weaponsmith()
    item = _rusty_item(faction=faction)

    result = get_item_upgrade_refusal(item=item, faction=faction, month=3, balance=1000)

    assert result is None


@pytest.mark.django_db
def test_get_item_upgrade_refusal_for_another_factions_item():
    faction = _faction_with_weaponsmith()
    item = _rusty_item(faction=FactionFactory(savegame=faction.savegame))

    result = get_item_upgrade_refusal(item=item, faction=faction, month=3, balance=1000)

    assert result == NOT_YOURS_REFUSAL


@pytest.mark.django_db
def test_get_item_upgrade_refusal_for_a_fallback_item():
    faction = _faction_with_weaponsmith()
    item = _rusty_item(faction=faction, type__is_fallback=True)

    result = get_item_upgrade_refusal(item=item, faction=faction, month=3, balance=1000)

    assert result == UNWORKABLE_REFUSAL


@pytest.mark.django_db
def test_get_item_upgrade_refusal_for_a_superior_item():
    faction = _faction_with_weaponsmith()
    item = ItemFactory(savegame=faction.savegame, owner=faction, condition=Item.ConditionChoices.CONDITION_SUPERIOR)

    result = get_item_upgrade_refusal(item=item, faction=faction, month=3, balance=1000)

    assert result == SUPERIOR_REFUSAL


@pytest.mark.django_db
def test_get_item_upgrade_refusal_without_a_weaponsmith():
    faction = _faction_with_weaponsmith(level=Town.WeaponsmithChoices.WEAPONSMITH_NONE)
    item = _rusty_item(faction=faction)

    result = get_item_upgrade_refusal(item=item, faction=faction, month=3, balance=1000)

    assert result == NO_WEAPONSMITH_REFUSAL


@pytest.mark.django_db
def test_get_item_upgrade_refusal_beyond_what_the_forge_reaches():
    faction = _faction_with_weaponsmith(level=Town.WeaponsmithChoices.WEAPONSMITH_SMALL)
    item = ItemFactory(savegame=faction.savegame, owner=faction, condition=Item.ConditionChoices.CONDITION_CHEAP)

    result = get_item_upgrade_refusal(item=item, faction=faction, month=3, balance=1000)

    assert result == BEYOND_THE_FORGE_REFUSAL


@pytest.mark.django_db
def test_get_item_upgrade_refusal_while_its_wearer_stands_in_an_open_fight():
    faction = _faction_with_weaponsmith()
    item = _rusty_item(faction=faction)
    warrior = WarriorFactory(faction=faction, weapon=item)
    skirmish = SkirmishFactory(attacking_faction=faction, victorious_faction=None)
    skirmish.attacking_warriors.add(warrior)

    result = get_item_upgrade_refusal(item=item, faction=faction, month=3, balance=1000)

    assert result == HOLDER_REFUSAL.format(name=warrior.display_name)


@pytest.mark.django_db
def test_get_item_upgrade_refusal_once_the_month_has_had_its_rework():
    faction = _faction_with_weaponsmith()
    Town.objects.filter(faction=faction).update(last_item_upgraded_at=3)
    faction.town.refresh_from_db()
    item = _rusty_item(faction=faction)

    result = get_item_upgrade_refusal(item=item, faction=faction, month=3, balance=1000)

    assert result == ALREADY_UPGRADED_THIS_MONTH_REFUSAL


@pytest.mark.django_db
def test_get_item_upgrade_refusal_when_the_purse_falls_short():
    faction = _faction_with_weaponsmith()
    item = _rusty_item(faction=faction)

    result = get_item_upgrade_refusal(item=item, faction=faction, month=3, balance=39)

    assert result == UNAFFORDABLE_REFUSAL


@pytest.mark.django_db
def test_get_item_upgrade_offer_prices_a_short_purse_on_the_button():
    faction = _faction_with_weaponsmith()
    item = _rusty_item(faction=faction)

    result = get_item_upgrade_offer(item=item, faction=faction, month=3, balance=39)

    assert result == {"upgrade": get_item_upgrade(item=item), "refusal": None, "can_afford": False}


@pytest.mark.django_db
def test_get_item_upgrade_offer_names_a_refusal_the_player_can_wait_out():
    faction = _faction_with_weaponsmith(level=Town.WeaponsmithChoices.WEAPONSMITH_SMALL)
    item = ItemFactory(savegame=faction.savegame, owner=faction, condition=Item.ConditionChoices.CONDITION_CHEAP)

    result = get_item_upgrade_offer(item=item, faction=faction, month=3, balance=1000)

    assert result["refusal"] == BEYOND_THE_FORGE_REFUSAL


@pytest.mark.django_db
def test_get_item_upgrade_offer_without_a_weaponsmith_offers_nothing():
    faction = _faction_with_weaponsmith(level=Town.WeaponsmithChoices.WEAPONSMITH_NONE)
    item = _rusty_item(faction=faction)

    result = get_item_upgrade_offer(item=item, faction=faction, month=3, balance=1000)

    assert result is None


def test_item_upgrade_condition_label_names_the_condition():
    upgrade = ItemUpgrade(condition=Item.ConditionChoices.CONDITION_TRADITIONAL, modifier=2, price=110, costs=40)

    assert upgrade.condition_label == "Traditional"
