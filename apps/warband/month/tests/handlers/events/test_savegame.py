from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.month.handlers.events.savegame import handle_log_savegame_ending
from apps.warband.month.messages.commands.month import CreatePlayerMonthLog
from apps.warband.month.models.player_month_log import PlayerMonthLog
from apps.warband.savegame.messages.events.savegame import SavegameEnded
from apps.warband.savegame.models.savegame import Savegame
from apps.warband.savegame.tests.factories.savegame import SavegameFactory


def test_handle_log_savegame_ending_narrates_a_defeat():
    faction = FactionFactory.build()

    result = handle_log_savegame_ending(
        context=SavegameEnded(
            savegame=SavegameFactory.build(),
            outcome=Savegame.OutcomeChoices.OUTCOME_LOST,
            player_faction=faction,
            open_skirmish_list=[],
            month=3,
        )
    )

    assert result == CreatePlayerMonthLog(
        title="The war band is broken.",
        body="Your faction is out of the game, and what is left of it answers to nobody.",
        kind=PlayerMonthLog.KindChoices.KIND_SAVEGAME_ENDED,
        month=3,
        faction=faction,
    )


def test_handle_log_savegame_ending_narrates_a_victory():
    faction = FactionFactory.build()

    result = handle_log_savegame_ending(
        context=SavegameEnded(
            savegame=SavegameFactory.build(),
            outcome=Savegame.OutcomeChoices.OUTCOME_WON,
            player_faction=faction,
            open_skirmish_list=[],
            month=3,
        )
    )

    assert result == CreatePlayerMonthLog(
        title="The last rival has fallen.",
        body="No war band is left standing against you. The country is yours.",
        kind=PlayerMonthLog.KindChoices.KIND_SAVEGAME_ENDED,
        month=3,
        faction=faction,
    )
