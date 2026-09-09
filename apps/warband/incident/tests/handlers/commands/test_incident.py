from unittest import mock

import pytest

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.incident.handlers.commands.incident import handle_choose_incident
from apps.warband.incident.incidents.boys_from_the_hundred import BoysFromTheHundred
from apps.warband.incident.incidents.plough_hoard import PloughHoard
from apps.warband.incident.incidents.toll_on_the_old_road import TollOnTheOldRoad
from apps.warband.incident.messages.commands.incident import ChooseIncident
from apps.warband.incident.messages.events.incident import IncidentOccurred


@pytest.mark.django_db
def test_handle_choose_incident_announces_what_was_drawn():
    faction = FactionFactory()

    with mock.patch("apps.warband.incident.handlers.commands.incident.random.choices", return_value=[PloughHoard]):
        result = handle_choose_incident(context=ChooseIncident(faction=faction, month=3))

    assert result == IncidentOccurred(faction=faction, month=3, outcome=PloughHoard.resolve(faction=faction))


@pytest.mark.django_db
def test_handle_choose_incident_on_a_quiet_month():
    """
    Nothing happening is a weight in the same draw, so the quiet month comes back as the drawn
    result rather than as a branch around the draw.
    """
    faction = FactionFactory()

    with mock.patch("apps.warband.incident.handlers.commands.incident.random.choices", return_value=[None]):
        result = handle_choose_incident(context=ChooseIncident(faction=faction, month=3))

    assert result is None


@pytest.mark.django_db
def test_handle_choose_incident_draws_only_from_what_is_possible():
    """
    A faction with no war band, no gear and an empty purse cannot be reached by the entries that
    need one of those, so they are not in the draw at all - and the quiet month is.
    """
    faction = FactionFactory(fyrd_reserve=0)

    with mock.patch(
        "apps.warband.incident.handlers.commands.incident.random.choices", return_value=[None]
    ) as mocked_draw:
        handle_choose_incident(context=ChooseIncident(faction=faction, month=3))

    assert mocked_draw.call_args.args[0] == (None, PloughHoard, TollOnTheOldRoad, BoysFromTheHundred)
