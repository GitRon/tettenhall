from apps.warband.faction.messages.events.faction import (
    CaptiveFledOverfullCells,
    FactionFyrdReserveReplenished,
    FactionLeaderRaisedFromFyrd,
    FactionLeaderSucceeded,
    FactionWasDefeated,
    MonthlyBuildingMoneyEarned,
    MonthlyWarriorSalariesPaid,
    MonthlyWarriorSalariesUnpaid,
)
from apps.warband.faction.messages.events.item import TownShopRestocked
from apps.warband.faction.messages.events.warrior import TownMercenariesRestocked
from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.month.handlers.events.faction import (
    handle_captive_fled_overfull_cells,
    handle_faction_fyrd_reserve_replenished,
    handle_log_faction_defeat,
    handle_log_leader_raised_from_fyrd,
    handle_log_leader_succession,
    handle_monthly_building_earnings,
    handle_pay_monthly_salary,
    handle_town_mercenaries_restocked,
    handle_town_shop_restocked,
    handle_unpaid_warrior_salaries,
)
from apps.warband.month.messages.commands.month import CreatePlayerMonthLog
from apps.warband.month.models.player_month_log import PlayerMonthLog
from apps.warband.savegame.tests.factories.savegame import SavegameFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory


def test_handle_faction_fyrd_reserve_replenished_logs_the_new_recruits():
    faction = FactionFactory.build()

    result = handle_faction_fyrd_reserve_replenished(
        context=FactionFyrdReserveReplenished(faction=faction, new_recruits=2, month=3)
    )

    assert result == CreatePlayerMonthLog(
        title="The fyrd has grown by 2 new recruits!",
        kind=PlayerMonthLog.KindChoices.KIND_FYRD_GROWTH,
        month=3,
        faction=faction,
    )


def test_handle_faction_fyrd_reserve_replenished_keeps_a_single_recruit_singular():
    faction = FactionFactory.build()

    result = handle_faction_fyrd_reserve_replenished(
        context=FactionFyrdReserveReplenished(faction=faction, new_recruits=1, month=3)
    )

    assert result == CreatePlayerMonthLog(
        title="The fyrd has grown by 1 new recruit!",
        kind=PlayerMonthLog.KindChoices.KIND_FYRD_GROWTH,
        month=3,
        faction=faction,
    )


def test_handle_pay_monthly_salary_logs_the_paid_amount():
    faction = FactionFactory.build()

    result = handle_pay_monthly_salary(context=MonthlyWarriorSalariesPaid(faction=faction, amount=250, month=3))

    assert result == CreatePlayerMonthLog(
        title="Monthly salaries of 250 silver paid.",
        kind=PlayerMonthLog.KindChoices.KIND_SALARIES_PAID,
        month=3,
        faction=faction,
    )


def test_handle_unpaid_warrior_salaries_logs_the_shortfall():
    """
    The one cost the player never chose to take on, so it gets said plainly - one line for the whole
    shortfall, with the men who walk getting their own lines elsewhere.
    """
    faction = FactionFactory.build()

    result = handle_unpaid_warrior_salaries(
        context=MonthlyWarriorSalariesUnpaid(
            faction=faction,
            warrior_list=[WarriorFactory.build(), WarriorFactory.build()],
            missing_amount=150,
            month=3,
        )
    )

    assert result == CreatePlayerMonthLog(
        title="150 silver short: 2 warriors went unpaid.",
        kind=PlayerMonthLog.KindChoices.KIND_UNPAID_SALARIES,
        month=3,
        faction=faction,
    )


def test_handle_unpaid_warrior_salaries_keeps_a_single_unpaid_warrior_singular():
    faction = FactionFactory.build()

    result = handle_unpaid_warrior_salaries(
        context=MonthlyWarriorSalariesUnpaid(
            faction=faction, warrior_list=[WarriorFactory.build()], missing_amount=150, month=3
        )
    )

    assert result == CreatePlayerMonthLog(
        title="150 silver short: 1 warrior went unpaid.",
        kind=PlayerMonthLog.KindChoices.KIND_UNPAID_SALARIES,
        month=3,
        faction=faction,
    )


def test_handle_log_faction_defeat_names_the_rival_leader_who_fell():
    player_faction = FactionFactory.build(name="Tettenhall")
    faction = FactionFactory.build(name="Kristinefoss")
    leader = WarriorFactory.build(name="Vincent")

    result = handle_log_faction_defeat(
        context=FactionWasDefeated(
            faction=faction,
            savegame=SavegameFactory.build(),
            player_faction=player_faction,
            leader=leader,
            leader_was_killed=True,
            month=3,
        )
    )

    assert result == CreatePlayerMonthLog(
        title="Kristinefoss is out of the war.",
        body="Vincent led them, and he fell in the fighting. There is nobody left to answer for the faction.",
        kind=PlayerMonthLog.KindChoices.KIND_RIVAL_DEFEATED,
        month=3,
        faction=player_faction,
    )


def test_handle_log_faction_defeat_names_a_captured_rival_leader_as_a_prisoner():
    player_faction = FactionFactory.build(name="Tettenhall")
    faction = FactionFactory.build(name="Kristinefoss")
    leader = WarriorFactory.build(name="Vincent")

    result = handle_log_faction_defeat(
        context=FactionWasDefeated(
            faction=faction,
            savegame=SavegameFactory.build(),
            player_faction=player_faction,
            leader=leader,
            leader_was_killed=False,
            month=3,
        )
    )

    assert result == CreatePlayerMonthLog(
        title="Kristinefoss is out of the war.",
        body="Vincent led them, and he is your prisoner. There is nobody left to answer for the faction.",
        kind=PlayerMonthLog.KindChoices.KIND_RIVAL_DEFEATED,
        month=3,
        faction=player_faction,
    )


def test_handle_log_faction_defeat_names_the_players_own_leader_who_fell():
    player_faction = FactionFactory.build(name="Tettenhall")
    leader = WarriorFactory.build(name="Reinfrith")

    result = handle_log_faction_defeat(
        context=FactionWasDefeated(
            faction=player_faction,
            savegame=SavegameFactory.build(),
            player_faction=player_faction,
            leader=leader,
            leader_was_killed=True,
            month=3,
        )
    )

    assert result == CreatePlayerMonthLog(
        title="Reinfrith fell in the fighting, and nobody is left to lead the war band.",
        kind=PlayerMonthLog.KindChoices.KIND_SAVEGAME_ENDED,
        month=3,
        faction=player_faction,
    )


def test_handle_log_faction_defeat_names_the_players_own_leader_taken_prisoner():
    player_faction = FactionFactory.build(name="Tettenhall")
    leader = WarriorFactory.build(name="Reinfrith")

    result = handle_log_faction_defeat(
        context=FactionWasDefeated(
            faction=player_faction,
            savegame=SavegameFactory.build(),
            player_faction=player_faction,
            leader=leader,
            leader_was_killed=False,
            month=3,
        )
    )

    assert result == CreatePlayerMonthLog(
        title="Reinfrith was taken prisoner, and nobody is left to lead the war band.",
        kind=PlayerMonthLog.KindChoices.KIND_SAVEGAME_ENDED,
        month=3,
        faction=player_faction,
    )


def test_handle_monthly_building_earnings_logs_the_earned_amount():
    faction = FactionFactory.build()

    result = handle_monthly_building_earnings(context=MonthlyBuildingMoneyEarned(faction=faction, amount=300, month=3))

    assert result == CreatePlayerMonthLog(
        title="Buildings earned 300 silver this month.",
        kind=PlayerMonthLog.KindChoices.KIND_BUILDING_INCOME,
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


def test_handle_log_leader_succession_for_the_players_own_war_band():
    player_faction = FactionFactory.build(name="Tettenhall")

    result = handle_log_leader_succession(
        context=FactionLeaderSucceeded(
            faction=player_faction,
            player_faction=player_faction,
            fallen_leader=WarriorFactory.build(name="Vincent"),
            successor=WarriorFactory.build(name="Beorn"),
            leader_was_killed=True,
            month=3,
        )
    )

    assert result == CreatePlayerMonthLog(
        title="Vincent fell in the fighting. Beorn leads the war band now.",
        body="He had the most renown of the men left, and they follow him.",
        kind=PlayerMonthLog.KindChoices.KIND_LEADER_SUCCEEDED,
        month=3,
        faction=player_faction,
    )


def test_handle_log_leader_succession_for_a_rival_whose_leader_was_taken():
    player_faction = FactionFactory.build(name="Tettenhall")

    result = handle_log_leader_succession(
        context=FactionLeaderSucceeded(
            faction=FactionFactory.build(name="Kristinefoss"),
            player_faction=player_faction,
            fallen_leader=WarriorFactory.build(name="Vincent"),
            successor=WarriorFactory.build(name="Beorn"),
            leader_was_killed=False,
            month=3,
        )
    )

    assert result == CreatePlayerMonthLog(
        title="Kristinefoss has a new Ealdorman.",
        body="Vincent led them, and he was taken prisoner. Beorn leads them now.",
        kind=PlayerMonthLog.KindChoices.KIND_LEADER_SUCCEEDED,
        month=3,
        faction=player_faction,
    )


def test_handle_log_leader_raised_from_fyrd_for_the_players_own_war_band():
    player_faction = FactionFactory.build(name="Tettenhall")

    result = handle_log_leader_raised_from_fyrd(
        context=FactionLeaderRaisedFromFyrd(
            faction=player_faction,
            player_faction=player_faction,
            fallen_leader=WarriorFactory.build(name="Vincent"),
            successor=WarriorFactory.build(name="Beorn"),
            leader_was_killed=True,
            month=3,
        )
    )

    assert result == CreatePlayerMonthLog(
        title="Vincent fell in the fighting. The fyrd has raised Beorn to lead the war band.",
        body="Nobody was left in the war band to follow, so the men of the land sent one of their own.",
        kind=PlayerMonthLog.KindChoices.KIND_LEADER_RAISED_FROM_FYRD,
        month=3,
        faction=player_faction,
    )


def test_handle_log_leader_raised_from_fyrd_for_a_rival_whose_leader_was_taken():
    player_faction = FactionFactory.build(name="Tettenhall")

    result = handle_log_leader_raised_from_fyrd(
        context=FactionLeaderRaisedFromFyrd(
            faction=FactionFactory.build(name="Kristinefoss"),
            player_faction=player_faction,
            fallen_leader=WarriorFactory.build(name="Vincent"),
            successor=WarriorFactory.build(name="Beorn"),
            leader_was_killed=False,
            month=3,
        )
    )

    assert result == CreatePlayerMonthLog(
        title="Kristinefoss has a new Ealdorman.",
        body="Vincent led them, and he was taken prisoner. Nobody was left in their war band, so their fyrd "
        "has raised Beorn to lead them.",
        kind=PlayerMonthLog.KindChoices.KIND_LEADER_RAISED_FROM_FYRD,
        month=3,
        faction=player_faction,
    )


def test_handle_captive_fled_overfull_cells_says_who_got_away_and_why():
    faction = FactionFactory.build()
    warrior = WarriorFactory.build(name="Wulfstan")

    result = handle_captive_fled_overfull_cells(
        context=CaptiveFledOverfullCells(faction=faction, warrior=warrior, cell_places=2, month=3)
    )

    assert result == CreatePlayerMonthLog(
        title="Wulfstan slipped away in the night: your cells hold 2.",
        kind=PlayerMonthLog.KindChoices.KIND_CAPTIVE_FLED,
        month=3,
        faction=faction,
    )
