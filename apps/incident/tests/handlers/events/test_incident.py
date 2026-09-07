import pytest

from apps.faction.messages.commands.faction import ChangeFyrdReserve
from apps.faction.tests.factories.faction import FactionFactory
from apps.finance.messages.commands.transaction import CreateTransaction
from apps.incident.handlers.events.incident import (
    handle_incident_fyrd_reserve,
    handle_incident_lost_item,
    handle_incident_max_morale,
    handle_incident_silver,
    handle_write_incident_to_month_log,
)
from apps.incident.incidents.base import IncidentOutcome
from apps.incident.messages.events.incident import IncidentOccurred
from apps.item.messages.commands.item import LoseItem
from apps.item.tests.factories.item import ItemFactory
from apps.month.messages.commands.month import CreatePlayerMonthLog
from apps.month.models.player_month_log import PlayerMonthLog
from apps.skirmish.tests.factories.warrior import WarriorFactory
from apps.warrior.messages.commands.warrior import ChangeWarriorMaxMorale


def test_handle_write_incident_to_month_log_carries_both_sentences():
    faction = FactionFactory.build()
    outcome = IncidentOutcome(title="The hall roof came down in the night.", body="Nobody was beneath it.")

    result = handle_write_incident_to_month_log(context=IncidentOccurred(faction=faction, month=3, outcome=outcome))

    assert result == CreatePlayerMonthLog(
        title="The hall roof came down in the night.",
        body="Nobody was beneath it.",
        kind=PlayerMonthLog.KindChoices.KIND_INCIDENT,
        month=3,
        faction=faction,
    )


def test_handle_incident_silver_books_what_it_cost():
    faction = FactionFactory.build()
    outcome = IncidentOutcome(title="The hall roof came down in the night.", body="", silver_change=-180)

    result = handle_incident_silver(context=IncidentOccurred(faction=faction, month=3, outcome=outcome))

    assert result == CreateTransaction(
        reason="The hall roof came down in the night.",
        amount=-180,
        faction=faction,
        month=3,
    )


def test_handle_incident_silver_for_an_incident_that_costs_nothing():
    faction = FactionFactory.build()

    result = handle_incident_silver(
        context=IncidentOccurred(faction=faction, month=3, outcome=IncidentOutcome(title="A relic.", body=""))
    )

    assert result is None


def test_handle_incident_fyrd_reserve_passes_the_change_on():
    faction = FactionFactory.build()
    outcome = IncidentOutcome(title="Villagers came in.", body="", fyrd_change=2)

    result = handle_incident_fyrd_reserve(context=IncidentOccurred(faction=faction, month=3, outcome=outcome))

    assert result == ChangeFyrdReserve(faction=faction, change=2, month=3)


def test_handle_incident_fyrd_reserve_for_an_incident_that_leaves_it_alone():
    faction = FactionFactory.build()

    result = handle_incident_fyrd_reserve(
        context=IncidentOccurred(faction=faction, month=3, outcome=IncidentOutcome(title="A relic.", body=""))
    )

    assert result is None


@pytest.mark.django_db
def test_handle_incident_max_morale_names_the_man_and_the_share():
    warrior = WarriorFactory()
    outcome = IncidentOutcome(title="A relic came.", body="", max_morale_share=0.2, warrior=warrior)

    result = handle_incident_max_morale(context=IncidentOccurred(faction=warrior.faction, month=3, outcome=outcome))

    assert result == ChangeWarriorMaxMorale(warrior=warrior, faction=warrior.faction, share=0.2, month=3)


@pytest.mark.django_db
def test_handle_incident_max_morale_for_an_incident_that_only_names_a_man():
    """
    Keyed on the share, not on the warrior: an entry may put a man in its title without touching
    his nerve.
    """
    warrior = WarriorFactory()
    outcome = IncidentOutcome(title="Wighelm has lost his spear.", body="", warrior=warrior)

    result = handle_incident_max_morale(context=IncidentOccurred(faction=warrior.faction, month=3, outcome=outcome))

    assert result is None


@pytest.mark.django_db
def test_handle_incident_lost_item_hands_the_gear_over_to_be_destroyed():
    faction = FactionFactory()
    lost_item = ItemFactory(owner=faction, savegame=faction.savegame)
    outcome = IncidentOutcome(title="Wighelm has lost his spear.", body="", lost_item=lost_item)

    result = handle_incident_lost_item(context=IncidentOccurred(faction=faction, month=3, outcome=outcome))

    assert result == LoseItem(faction=faction, item=lost_item, month=3)


def test_handle_incident_lost_item_for_an_incident_that_takes_no_gear():
    faction = FactionFactory.build()

    result = handle_incident_lost_item(
        context=IncidentOccurred(faction=faction, month=3, outcome=IncidentOutcome(title="A relic.", body=""))
    )

    assert result is None
