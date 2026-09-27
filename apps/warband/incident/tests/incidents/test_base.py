"""
What every entry of the catalogue inherits, exercised through the entries that inherit it.

No test-only subclass of [Incident]: the shared behaviour is a default weight, a default
precondition and a default resolve, and each of those is worth more asserted through a real entry
than through one written to make the assert pass.
"""

import pytest

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.finance.tests.factories.transaction import TransactionFactory
from apps.warband.incident.incidents.abbot_asks_for_lead import AbbotAsksForLead
from apps.warband.incident.incidents.base import IncidentOutcome, IncidentQuestion, losable_items, roster
from apps.warband.incident.incidents.burnt_village_refugees import BurntVillageRefugees
from apps.warband.incident.incidents.hall_roof_falls_in import HallRoofFallsIn
from apps.warband.incident.incidents.plough_hoard import PloughHoard
from apps.warband.incident.incidents.toll_on_the_old_road import TollOnTheOldRoad
from apps.warband.incident.tests.factories.pending_incident import PendingIncidentFactory
from apps.warband.item.models.item_type import ItemType
from apps.warband.item.tests.factories.item import ItemFactory
from apps.warband.item.tests.factories.item_type import ItemTypeFactory
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_roster_holds_the_living_men_of_the_faction():
    faction = FactionFactory()
    warrior = WarriorFactory(faction=faction)

    assert roster(faction=faction) == [warrior]


@pytest.mark.django_db
def test_roster_excludes_the_dead():
    """
    Dying does not clear "Warrior.faction", so without this a relic is handed to a corpse.
    """
    faction = FactionFactory()
    WarriorFactory(faction=faction, condition=Warrior.ConditionChoices.CONDITION_DEAD)

    assert roster(faction=faction) == []


@pytest.mark.django_db
def test_roster_excludes_another_factions_men():
    """
    Without the faction filter, a relic reaches a rival's warrior and a chronicle line names him.
    """
    faction = FactionFactory()
    WarriorFactory(faction=FactionFactory(savegame=faction.savegame))

    assert roster(faction=faction) == []


@pytest.mark.django_db
def test_losable_items_excludes_the_finest_of_each_function():
    faction = FactionFactory()
    finest_weapon = ItemFactory(owner=faction, savegame=faction.savegame, price=200)
    cheap_weapon = ItemFactory(owner=faction, savegame=faction.savegame, price=30)
    WarriorFactory(faction=faction, weapon=finest_weapon)
    WarriorFactory(faction=faction, weapon=cheap_weapon)

    assert losable_items(faction=faction) == [cheap_weapon]


@pytest.mark.django_db
def test_losable_items_counts_weapons_and_armour_separately():
    """
    One of each in the field means both are the finest of their function, so neither is losable.
    """
    faction = FactionFactory()
    weapon = ItemFactory(owner=faction, savegame=faction.savegame)
    armor = ItemFactory(
        owner=faction,
        savegame=faction.savegame,
        type=ItemTypeFactory(function=ItemType.FunctionChoices.FUNCTION_ARMOR),
    )
    WarriorFactory(faction=faction, weapon=weapon, armor=armor)

    assert losable_items(faction=faction) == []


@pytest.mark.django_db
def test_losable_items_ignores_gear_nobody_carries():
    """
    An item no warrior wears is in a chest at home, not out on a moor.
    """
    faction = FactionFactory()
    worn_weapon = ItemFactory(owner=faction, savegame=faction.savegame, price=200)
    ItemFactory(owner=faction, savegame=faction.savegame, price=30)
    WarriorFactory(faction=faction, weapon=worn_weapon)

    assert losable_items(faction=faction) == []


@pytest.mark.django_db
def test_losable_items_excludes_another_factions_gear():
    """
    Without the owner filter, a moor swallows a rival's spear and the row deleted is not the acting
    faction's to lose.
    """
    faction = FactionFactory()
    rival_faction = FactionFactory(savegame=faction.savegame)
    WarriorFactory(
        faction=rival_faction,
        weapon=ItemFactory(owner=rival_faction, savegame=faction.savegame, price=200),
    )
    WarriorFactory(
        faction=rival_faction,
        weapon=ItemFactory(owner=rival_faction, savegame=faction.savegame, price=30),
    )

    assert losable_items(faction=faction) == []


@pytest.mark.django_db
def test_is_possible_for_an_entry_with_nothing_to_take():
    faction = FactionFactory()

    assert PloughHoard.is_possible(faction=faction) is True


@pytest.mark.django_db
def test_is_possible_for_a_cost_the_treasury_covers():
    faction = FactionFactory()
    TransactionFactory(faction=faction, amount=-HallRoofFallsIn.SILVER_CHANGE)

    assert HallRoofFallsIn.is_possible(faction=faction) is True


@pytest.mark.django_db
def test_is_possible_for_a_cost_the_treasury_does_not_cover():
    """
    An incident must not open a hole the player did not dig, so a cost he cannot pay does not happen
    to him at all.
    """
    faction = FactionFactory()
    TransactionFactory(faction=faction, amount=-HallRoofFallsIn.SILVER_CHANGE - 1)

    assert HallRoofFallsIn.is_possible(faction=faction) is False


def test_is_question_for_an_entry_declaring_options():
    assert AbbotAsksForLead.is_question() is True


def test_is_question_for_a_notice():
    assert PloughHoard.is_question() is False


def test_get_option_by_its_key():
    assert AbbotAsksForLead.get_option(key="give") == AbbotAsksForLead.OPTIONS[0]


def test_get_option_for_a_key_naming_nothing():
    """
    A posted key is checked here, so one naming no option has to come back as nothing rather than
    as the first option or an error.
    """
    assert AbbotAsksForLead.get_option(key="burn_the_minster") is None


def test_get_default_option():
    assert AbbotAsksForLead.get_default_option() == AbbotAsksForLead.OPTIONS[1]


@pytest.mark.django_db
def test_is_possible_for_a_question_whose_dearest_answer_the_treasury_covers():
    faction = FactionFactory()
    TransactionFactory(faction=faction, amount=-AbbotAsksForLead.OPTIONS[0].silver_change)

    assert AbbotAsksForLead.is_possible(faction=faction) is True


@pytest.mark.django_db
def test_is_possible_for_a_question_whose_dearest_answer_the_treasury_does_not_cover():
    """
    A question is priced by its dearest answer: asking a player who can only give the other one
    is a notice with a button that cannot be pressed.
    """
    faction = FactionFactory()
    TransactionFactory(faction=faction, amount=-AbbotAsksForLead.OPTIONS[0].silver_change - 1)

    assert AbbotAsksForLead.is_possible(faction=faction) is False


@pytest.mark.django_db
def test_resolve_turns_the_constants_into_an_outcome():
    """
    An entry whose outcome depends on nothing needs no code of its own, which is what keeps adding
    one to a single class.
    """
    faction = FactionFactory()

    result = TollOnTheOldRoad.resolve(faction=faction)

    assert result == IncidentOutcome(
        title=TollOnTheOldRoad.TITLE,
        body=TollOnTheOldRoad.BODY,
        silver_change=TollOnTheOldRoad.SILVER_CHANGE,
    )


@pytest.mark.django_db
def test_ask_turns_the_constants_into_a_question():
    faction = FactionFactory()

    result = AbbotAsksForLead.ask(faction=faction)

    assert result == IncidentQuestion(title=AbbotAsksForLead.TITLE, body=AbbotAsksForLead.BODY)


@pytest.mark.django_db
def test_answer_turns_the_option_into_an_outcome():
    option = BurntVillageRefugees.get_option(key="take_in")
    pending_incident = PendingIncidentFactory()

    result = BurntVillageRefugees.answer(option=option, pending_incident=pending_incident)

    assert result == IncidentOutcome(
        title=option.title,
        body=option.body,
        silver_change=option.silver_change,
        fyrd_change=option.fyrd_change,
    )


@pytest.mark.django_db
def test_answer_clamps_a_levy_to_the_reserve():
    """
    Resolved when the answer lands, so the command is never asked for men who are no longer there.
    """
    option = AbbotAsksForLead.get_option(key="refuse")
    pending_incident = PendingIncidentFactory(faction__fyrd_reserve=0, incident=AbbotAsksForLead.__name__)

    result = AbbotAsksForLead.answer(option=option, pending_incident=pending_incident)

    assert result.fyrd_change == 0
