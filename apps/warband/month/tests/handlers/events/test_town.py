from apps.warband.month.handlers.events.town import handle_feast_thrown, handle_geld_called
from apps.warband.month.messages.commands.month import CreatePlayerMonthLog
from apps.warband.month.models.player_month_log import PlayerMonthLog
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.town.messages.events.town import FeastThrown, GeldCalled
from apps.warband.town.models import Town
from apps.warband.town.tests.factories.town import TownFactory


def _feast(*, warrior_list: list, costs: int) -> FeastThrown:
    town = TownFactory.build(hall=Town.HallChoices.HALL_MEDIUM)
    return FeastThrown(
        town=town, faction=town.faction, warrior_list=warrior_list, restored_share=0.2, costs=costs, month=5
    )


def test_handle_feast_thrown_names_the_bill_and_the_men_it_mended():
    cut = WarriorFactory.build(max_morale=15, peak_max_morale=20)
    whole = WarriorFactory.build(max_morale=20, peak_max_morale=20)
    context = _feast(warrior_list=[cut, whole], costs=30)

    result = handle_feast_thrown(context=context)

    assert result == CreatePlayerMonthLog(
        title="A feast in the Great Hall fed 2 men for 30 silver and mended the nerve of 1.",
        kind=PlayerMonthLog.KindChoices.KIND_FEAST_THROWN,
        month=5,
        faction=context.faction,
    )


def test_handle_feast_thrown_says_nothing_of_mending_when_nobody_needed_it():
    whole = WarriorFactory.build(max_morale=20, peak_max_morale=20)

    result = handle_feast_thrown(context=_feast(warrior_list=[whole], costs=15))

    assert result.title == "A feast in the Great Hall fed 1 man for 15 silver."


def test_handle_geld_called_names_the_silver_and_the_name_it_cost():
    town = TownFactory.build()
    context = GeldCalled(town=town, faction=town.faction, silver=80, fyrd_names=1, month=5)

    result = handle_geld_called(context=context)

    assert result == CreatePlayerMonthLog(
        title="The village paid a geld of 80 silver for 1 name off the fyrd roll.",
        kind=PlayerMonthLog.KindChoices.KIND_GELD_CALLED,
        month=5,
        faction=town.faction,
    )
