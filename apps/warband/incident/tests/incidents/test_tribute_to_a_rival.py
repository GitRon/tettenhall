from unittest import mock

import pytest

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.finance.tests.factories.transaction import TransactionFactory
from apps.warband.incident.incidents.base import IncidentQuestion
from apps.warband.incident.incidents.tribute_to_a_rival import TributeToARival
from apps.warband.incident.tests.factories.pending_incident import PendingIncidentFactory


@pytest.mark.django_db
def test_is_possible_with_a_rival_on_the_board_and_the_silver_to_pay():
    faction = FactionFactory()
    FactionFactory(savegame=faction.savegame)
    TransactionFactory(faction=faction, amount=-TributeToARival.get_option(key="pay").silver_change)

    assert TributeToARival.is_possible(faction=faction) is True


@pytest.mark.django_db
def test_is_possible_once_every_rival_is_knocked_out():
    """
    A defeated rival has no army left to ask with.
    """
    faction = FactionFactory()
    FactionFactory(savegame=faction.savegame, is_defeated=True)
    TransactionFactory(faction=faction, amount=-TributeToARival.get_option(key="pay").silver_change)

    assert TributeToARival.is_possible(faction=faction) is False


@pytest.mark.django_db
def test_is_possible_without_the_silver_to_pay():
    faction = FactionFactory()
    FactionFactory(savegame=faction.savegame)

    assert TributeToARival.is_possible(faction=faction) is False


@pytest.mark.django_db
def test_ask_names_the_rival_who_asked():
    faction = FactionFactory()
    rival = FactionFactory(savegame=faction.savegame, name="Hwicce")

    with mock.patch("apps.warband.incident.incidents.tribute_to_a_rival.random.choice", return_value=rival):
        result = TributeToARival.ask(faction=faction)

    assert result == IncidentQuestion(
        title="Hwicce asked for tribute, with an army behind the asking.",
        body=TributeToARival.BODY,
        rival=rival,
    )


@pytest.mark.django_db
def test_answer_names_the_rival_the_question_was_about():
    """
    The answer lands on the rival who asked, which is why the pending row keeps him.
    """
    pending_incident = PendingIncidentFactory(incident=TributeToARival.__name__, rival=FactionFactory(name="Hwicce"))

    result = TributeToARival.answer(option=TributeToARival.get_option(key="refuse"), pending_incident=pending_incident)

    assert result.title == "Tribute was refused to Hwicce, who took it out on the land."
