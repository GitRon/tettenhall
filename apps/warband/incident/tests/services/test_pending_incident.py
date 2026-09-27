import pytest

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.finance.tests.factories.transaction import TransactionFactory
from apps.warband.incident.incidents.burnt_village_refugees import BurntVillageRefugees
from apps.warband.incident.incidents.frisian_trader_wants_mail import FrisianTraderWantsMail
from apps.warband.incident.services.pending_incident import (
    OpenQuestion,
    get_open_questions,
    get_pending_incident_answer_refusal,
)
from apps.warband.incident.tests.factories.pending_incident import PendingIncidentFactory
from apps.warband.item.tests.factories.item import ItemFactory


@pytest.mark.django_db
def test_get_open_questions_carries_the_options_of_each_entry():
    pending_incident = PendingIncidentFactory()

    result = get_open_questions(faction_id=pending_incident.faction_id)

    assert result == [OpenQuestion(pending_incident=pending_incident, options=BurntVillageRefugees.OPTIONS)]


@pytest.mark.django_db
def test_get_pending_incident_answer_refusal_for_an_answer_that_can_be_given():
    pending_incident = PendingIncidentFactory()
    TransactionFactory(faction=pending_incident.faction, amount=120)

    result = get_pending_incident_answer_refusal(
        pending_incident=pending_incident, option=BurntVillageRefugees.get_option(key="take_in")
    )

    assert result is None


@pytest.mark.django_db
def test_get_pending_incident_answer_refusal_once_the_silver_is_spent():
    """
    The question was only asked of a player who could pay, but the month went on while it waited.
    """
    pending_incident = PendingIncidentFactory()
    TransactionFactory(faction=pending_incident.faction, amount=119)

    result = get_pending_incident_answer_refusal(
        pending_incident=pending_incident, option=BurntVillageRefugees.get_option(key="take_in")
    )

    assert result == "The treasury no longer covers that answer."


@pytest.mark.django_db
def test_get_pending_incident_answer_refusal_for_gear_still_held():
    faction = FactionFactory()
    pending_incident = PendingIncidentFactory(
        faction=faction,
        incident=FrisianTraderWantsMail.__name__,
        item=ItemFactory(owner=faction, savegame=faction.savegame),
    )

    result = get_pending_incident_answer_refusal(
        pending_incident=pending_incident, option=FrisianTraderWantsMail.get_option(key="sell")
    )

    assert result is None


@pytest.mark.django_db
def test_get_pending_incident_answer_refusal_for_gear_that_is_gone():
    pending_incident = PendingIncidentFactory(incident=FrisianTraderWantsMail.__name__, item=None)

    result = get_pending_incident_answer_refusal(
        pending_incident=pending_incident, option=FrisianTraderWantsMail.get_option(key="sell")
    )

    assert result == "That piece of gear is no longer yours to sell."


@pytest.mark.django_db
def test_get_pending_incident_answer_refusal_for_gear_that_changed_hands():
    """
    Sold to the shop, or taken in a fight: the row still points at the piece, but it is somebody
    else's now, and handing it to the trader would delete another faction's gear.
    """
    faction = FactionFactory()
    pending_incident = PendingIncidentFactory(
        faction=faction,
        incident=FrisianTraderWantsMail.__name__,
        item=ItemFactory(owner=FactionFactory(savegame=faction.savegame), savegame=faction.savegame),
    )

    result = get_pending_incident_answer_refusal(
        pending_incident=pending_incident, option=FrisianTraderWantsMail.get_option(key="sell")
    )

    assert result == "That piece of gear is no longer yours to sell."
