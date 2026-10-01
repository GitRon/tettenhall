from queuebie import message_registry
from queuebie.messages import Command

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
from apps.warband.faction.messages.events.quest import BulletinBoardQuestsOffered
from apps.warband.faction.messages.events.warrior import TownMercenariesRestocked
from apps.warband.month.messages.commands.month import CreatePlayerMonthLog
from apps.warband.month.models.player_month_log import PlayerMonthLog


@message_registry.register_event(event=CaptiveFledOverfullCells)
def handle_captive_fled_overfull_cells(*, context: CaptiveFledOverfullCells) -> Command:
    # Says why, so the first man lost to full cells is also the moment the player learns there are cells
    return CreatePlayerMonthLog(
        title=f"{context.warrior} slipped away in the night: your cells hold {context.cell_places}.",
        kind=PlayerMonthLog.KindChoices.KIND_CAPTIVE_FLED,
        month=context.month,
        faction=context.faction,
    )


@message_registry.register_event(event=FactionFyrdReserveReplenished)
def handle_faction_fyrd_reserve_replenished(*, context: FactionFyrdReserveReplenished) -> Command:
    return CreatePlayerMonthLog(
        # The handler only fires for one man upwards, but "1 new recruits" still read wrong
        title=f"The fyrd has grown by {context.new_recruits} new recruit{'' if context.new_recruits == 1 else 's'}!",
        kind=PlayerMonthLog.KindChoices.KIND_FYRD_GROWTH,
        month=context.month,
        faction=context.faction,
    )


@message_registry.register_event(event=MonthlyWarriorSalariesPaid)
def handle_pay_monthly_salary(*, context: MonthlyWarriorSalariesPaid) -> Command:
    return CreatePlayerMonthLog(
        title=f"Monthly salaries of {context.amount} silver paid.",
        kind=PlayerMonthLog.KindChoices.KIND_SALARIES_PAID,
        month=context.month,
        faction=context.faction,
    )


@message_registry.register_event(event=MonthlyWarriorSalariesUnpaid)
def handle_unpaid_warrior_salaries(*, context: MonthlyWarriorSalariesUnpaid) -> Command:
    # The one cost in the game the player never chose to take on, so it gets said plainly. One line
    # for the whole shortfall rather than one per man: the men who walk get their own lines, and the
    # ones who only lost heart are visible on the roster
    unpaid_warriors = len(context.warrior_list)

    return CreatePlayerMonthLog(
        title=f"{context.missing_amount} silver short: "
        f"{unpaid_warriors} warrior{'' if unpaid_warriors == 1 else 's'} went unpaid.",
        kind=PlayerMonthLog.KindChoices.KIND_UNPAID_SALARIES,
        month=context.month,
        faction=context.faction,
    )


@message_registry.register_event(event=FactionWasDefeated)
def handle_log_faction_defeat(*, context: FactionWasDefeated) -> Command:
    """
    Says that a faction is out of the game, and which man's loss did it.

    For a rival, the knockout is otherwise invisible: its row drops off the rivals list because a
    defeated faction stops getting a month. It says who fell and which faction he led, because the
    causal link between the man the player put down and the faction leaving the war is the part he
    cannot reconstruct - the battle report names the prisoner and says nothing about what taking him
    ended.

    For the player's own faction it is the cause, and the SavegameEnded line that follows is the
    verdict. A leader can be seated and lost again in the same fight - the man who took over lying
    senseless is taken with the rest when it is lost - and without this line the log goes from naming
    him the leader straight to the war band being broken. The kind is the ending's own, because this
    line is part of how the game ended.
    """
    # The instances rather than their ids: Django compares two unsaved rows by identity instead of
    # by a primary key they both lack, so this stays right for a handler called with built factions
    if context.faction == context.player_faction:
        fate = "fell in the fighting" if context.leader_was_killed else "was taken prisoner"

        return CreatePlayerMonthLog(
            title=f"{context.leader} {fate}, and nobody is left to lead the war band.",
            kind=PlayerMonthLog.KindChoices.KIND_SAVEGAME_ENDED,
            month=context.month,
            faction=context.player_faction,
        )

    if context.leader_was_killed:
        fate = f"{context.leader} led them, and he fell in the fighting."
    else:
        fate = f"{context.leader} led them, and he is your prisoner."

    return CreatePlayerMonthLog(
        title=f"{context.faction} is out of the war.",
        body=f"{fate} There is nobody left to answer for the faction.",
        kind=PlayerMonthLog.KindChoices.KIND_RIVAL_DEFEATED,
        month=context.month,
        faction=context.player_faction,
    )


@message_registry.register_event(event=FactionLeaderSucceeded)
def handle_log_leader_succession(*, context: FactionLeaderSucceeded) -> Command:
    """
    Says who fell and who leads now, for the player's own war band and for a rival alike.

    The player's own line matters most: a fallen leader used to end his savegame, and now the game
    goes on under a man he did not pick. A rival's matters because the man he just put down did not
    knock that faction out, and the one he has to beat next is named here.
    """
    fate = "fell in the fighting" if context.leader_was_killed else "was taken prisoner"

    # The instances rather than their ids, for the reason handle_log_faction_defeat gives
    if context.faction == context.player_faction:
        title = f"{context.fallen_leader} {fate}. {context.successor} leads the war band now."
        body = "He had the most renown of the men left, and they follow him."
    else:
        title = f"{context.faction} has a new leader."
        body = f"{context.fallen_leader} led them, and he {fate}. {context.successor} leads them now."

    return CreatePlayerMonthLog(
        title=title,
        body=body,
        kind=PlayerMonthLog.KindChoices.KIND_LEADER_SUCCEEDED,
        month=context.month,
        faction=context.player_faction,
    )


@message_registry.register_event(event=FactionLeaderRaisedFromFyrd)
def handle_log_leader_raised_from_fyrd(*, context: FactionLeaderRaisedFromFyrd) -> Command:
    """
    Says who fell, and that the faction's fyrd has raised a levy in his place because nobody was left.

    Its own line rather than the succession's, because the player has to read it differently: the
    faction he beat ran out of men and was not knocked out, and the man he has to beat next is a levy
    out of the fields rather than a veteran of its war band.
    """
    fate = "fell in the fighting" if context.leader_was_killed else "was taken prisoner"

    # The instances rather than their ids, for the reason handle_log_faction_defeat gives
    if context.faction == context.player_faction:
        title = f"{context.fallen_leader} {fate}. The fyrd has raised {context.successor} to lead the war band."
        body = "Nobody was left in the war band to follow, so the men of the land sent one of their own."
    else:
        title = f"{context.faction} has a new leader."
        body = (
            f"{context.fallen_leader} led them, and he {fate}. Nobody was left in their war band, so their "
            f"fyrd has raised {context.successor} to lead them."
        )

    return CreatePlayerMonthLog(
        title=title,
        body=body,
        kind=PlayerMonthLog.KindChoices.KIND_LEADER_RAISED_FROM_FYRD,
        month=context.month,
        faction=context.player_faction,
    )


@message_registry.register_event(event=MonthlyBuildingMoneyEarned)
def handle_monthly_building_earnings(*, context: MonthlyBuildingMoneyEarned) -> Command:
    return CreatePlayerMonthLog(
        title=f"Buildings earned {context.amount} silver this month.",
        kind=PlayerMonthLog.KindChoices.KIND_BUILDING_INCOME,
        month=context.month,
        faction=context.faction,
    )


@message_registry.register_event(event=BulletinBoardQuestsOffered)
def handle_bulletin_board_quests_offered(*, context: BulletinBoardQuestsOffered) -> Command:
    return CreatePlayerMonthLog(
        title=f"The bulletin board is offering {context.new_quests} new quest{'' if context.new_quests == 1 else 's'}.",
        kind=PlayerMonthLog.KindChoices.KIND_QUESTS_OFFERED,
        month=context.month,
        faction=context.faction,
    )


@message_registry.register_event(event=TownMercenariesRestocked)
def handle_town_mercenaries_restocked(*, context: TownMercenariesRestocked) -> Command:
    return CreatePlayerMonthLog(
        title=f"The pub has filled with {context.new_mercenaries} "
        f"mercenar{'y' if context.new_mercenaries == 1 else 'ies'} for hire.",
        kind=PlayerMonthLog.KindChoices.KIND_PUB_RESTOCKED,
        month=context.month,
        faction=context.faction,
    )


@message_registry.register_event(event=TownShopRestocked)
def handle_town_shop_restocked(*, context: TownShopRestocked) -> Command:
    return CreatePlayerMonthLog(
        title=f"The shop has taken {context.new_items} new item{'' if context.new_items == 1 else 's'} into stock.",
        kind=PlayerMonthLog.KindChoices.KIND_SHOP_RESTOCKED,
        month=context.month,
        faction=context.faction,
    )
