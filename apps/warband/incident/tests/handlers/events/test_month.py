from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.incident.handlers.events.month import handle_choose_incident_for_new_month
from apps.warband.incident.messages.commands.incident import ChooseIncident
from apps.warband.month.messages.events.month import PlayerMonthPrepared
from apps.warband.savegame.tests.factories.savegame import SavegameFactory


def test_handle_choose_incident_for_new_month_maps_to_command():
    faction = FactionFactory.build()
    context = PlayerMonthPrepared(faction=faction, savegame=SavegameFactory.build(), current_month=7)

    result = handle_choose_incident_for_new_month(context=context)

    assert result == ChooseIncident(faction=faction, month=7)
