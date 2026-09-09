from apps.warband.faction.handlers.events.quest import handle_offer_new_quests_on_bulletin_board
from apps.warband.faction.messages.commands.quest import OfferNewQuestsOnBulletinBoard
from apps.warband.faction.messages.events.faction import NewFactionCreated
from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.month.messages.events.month import PlayerMonthPrepared
from apps.warband.savegame.tests.factories.savegame import SavegameFactory


def test_handle_offer_new_quests_on_bulletin_board_maps_to_command():
    """
    Pure mapping handler: it only reads from the message, so built instances are enough and no
    database is needed.
    """
    faction = FactionFactory.build()
    context = PlayerMonthPrepared(faction=faction, savegame=SavegameFactory.build(), current_month=7)

    result = handle_offer_new_quests_on_bulletin_board(context=context)

    assert result == OfferNewQuestsOnBulletinBoard(faction=faction, month=7)


def test_handle_offer_new_quests_on_bulletin_board_maps_a_created_faction_to_the_same_command():
    """
    The handler's second registration, which fires for every faction the bootstrap makes. Both
    messages have to carry "faction" and "current_month" for it to read them, and one test per
    registered message is what pins that.
    """
    faction = FactionFactory.build()
    context = NewFactionCreated(faction=faction, current_month=7)

    result = handle_offer_new_quests_on_bulletin_board(context=context)

    assert result == OfferNewQuestsOnBulletinBoard(faction=faction, month=7)
