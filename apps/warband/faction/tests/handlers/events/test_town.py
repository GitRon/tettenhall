from apps.warband.faction.handlers.events.town import handle_geld_strikes_names_off_the_fyrd
from apps.warband.faction.messages.commands.faction import ChangeFyrdReserve
from apps.warband.town.messages.events.town import GeldCalled
from apps.warband.town.tests.factories.town import TownFactory


def test_handle_geld_strikes_names_off_the_fyrd_takes_the_names_paid_with():
    town = TownFactory.build()

    result = handle_geld_strikes_names_off_the_fyrd(
        context=GeldCalled(town=town, faction=town.faction, silver=80, fyrd_names=1, month=4)
    )

    assert result == ChangeFyrdReserve(faction=town.faction, change=-1, month=4)
