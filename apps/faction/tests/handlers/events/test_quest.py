from apps.faction.handlers.events.quest import handle_offer_new_quests_on_bulletin_board
from apps.faction.messages.commands.quest import OfferNewQuestsOnBulletinBoard
from apps.faction.tests.factories.faction import FactionFactory
from apps.month.messages.events.month import MonthPrepared
from apps.savegame.tests.factories.savegame import SavegameFactory
from apps.training.tests.factories.training import TrainingFactory


def test_handle_offer_new_quests_on_bulletin_board_maps_to_command():
    """
    Pure mapping handler: it only reads from the message, so built instances are enough and no
    database is needed.
    """
    faction = FactionFactory.build()
    context = MonthPrepared(
        faction=faction, savegame=SavegameFactory.build(), training=TrainingFactory.build(), current_month=7
    )

    result = handle_offer_new_quests_on_bulletin_board(context=context)

    assert result == OfferNewQuestsOnBulletinBoard(faction=faction, month=7)
