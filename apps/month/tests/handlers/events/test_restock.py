from apps.faction.messages.events.item import TownShopRestocked
from apps.faction.messages.events.quest import BulletinBoardQuestsOffered
from apps.faction.messages.events.warrior import TownMercenariesRestocked
from apps.faction.tests.factories.faction import FactionFactory
from apps.month.handlers.events.restock import (
    handle_bulletin_board_quests_offered,
    handle_town_mercenaries_restocked,
    handle_town_shop_restocked,
)
from apps.month.messages.commands.month import CreatePlayerMonthLog
from apps.month.models.player_month_log import PlayerMonthLog


def test_handle_bulletin_board_quests_offered_logs_the_new_quests():
    faction = FactionFactory.build()

    result = handle_bulletin_board_quests_offered(
        context=BulletinBoardQuestsOffered(faction=faction, new_quests=3, month=3)
    )

    assert result == CreatePlayerMonthLog(
        title="The bulletin board is offering 3 new quests.",
        kind=PlayerMonthLog.KindChoices.KIND_QUESTS_OFFERED,
        month=3,
        faction=faction,
    )


def test_handle_bulletin_board_quests_offered_keeps_a_single_quest_singular():
    faction = FactionFactory.build()

    result = handle_bulletin_board_quests_offered(
        context=BulletinBoardQuestsOffered(faction=faction, new_quests=1, month=3)
    )

    assert result == CreatePlayerMonthLog(
        title="The bulletin board is offering 1 new quest.",
        kind=PlayerMonthLog.KindChoices.KIND_QUESTS_OFFERED,
        month=3,
        faction=faction,
    )


def test_handle_town_mercenaries_restocked_logs_the_men_for_hire():
    faction = FactionFactory.build()

    result = handle_town_mercenaries_restocked(
        context=TownMercenariesRestocked(faction=faction, new_mercenaries=2, month=3)
    )

    assert result == CreatePlayerMonthLog(
        title="The pub has filled with 2 mercenaries for hire.",
        kind=PlayerMonthLog.KindChoices.KIND_PUB_RESTOCKED,
        month=3,
        faction=faction,
    )


def test_handle_town_mercenaries_restocked_keeps_a_single_mercenary_singular():
    faction = FactionFactory.build()

    result = handle_town_mercenaries_restocked(
        context=TownMercenariesRestocked(faction=faction, new_mercenaries=1, month=3)
    )

    assert result == CreatePlayerMonthLog(
        title="The pub has filled with 1 mercenary for hire.",
        kind=PlayerMonthLog.KindChoices.KIND_PUB_RESTOCKED,
        month=3,
        faction=faction,
    )


def test_handle_town_shop_restocked_logs_the_new_stock():
    faction = FactionFactory.build()

    result = handle_town_shop_restocked(context=TownShopRestocked(faction=faction, new_items=4, month=3))

    assert result == CreatePlayerMonthLog(
        title="The shop has taken 4 new items into stock.",
        kind=PlayerMonthLog.KindChoices.KIND_SHOP_RESTOCKED,
        month=3,
        faction=faction,
    )


def test_handle_town_shop_restocked_keeps_a_single_item_singular():
    faction = FactionFactory.build()

    result = handle_town_shop_restocked(context=TownShopRestocked(faction=faction, new_items=1, month=3))

    assert result == CreatePlayerMonthLog(
        title="The shop has taken 1 new item into stock.",
        kind=PlayerMonthLog.KindChoices.KIND_SHOP_RESTOCKED,
        month=3,
        faction=faction,
    )
