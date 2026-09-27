from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.month.handlers.events.month import handle_log_harvest_for_new_month
from apps.warband.month.messages.commands.month import CreatePlayerMonthLog
from apps.warband.month.messages.events.month import FactionMonthPrepared
from apps.warband.month.models.player_month_log import PlayerMonthLog


def test_handle_log_harvest_for_new_month_in_haligmonath():
    """Month 6 is Haligmonath."""
    faction = FactionFactory.build()

    result = handle_log_harvest_for_new_month(context=FactionMonthPrepared(faction=faction, current_month=6))

    assert result == CreatePlayerMonthLog(
        title="The harvest is in, and it brought 100 silver.",
        kind=PlayerMonthLog.KindChoices.KIND_HARVEST,
        month=6,
        faction=faction,
    )


def test_handle_log_harvest_for_new_month_outside_the_harvest():
    result = handle_log_harvest_for_new_month(
        context=FactionMonthPrepared(faction=FactionFactory.build(), current_month=7)
    )

    assert result is None
