from queuebie import message_registry
from queuebie.messages import Command

from apps.warband.faction.messages.events.faction import (
    FactionFyrdReserveReplenished,
    FactionWasDefeated,
    MonthlyBuildingMoneyEarned,
    MonthlyWarriorSalariesPaid,
    MonthlyWarriorSalariesUnpaid,
)
from apps.warband.month.messages.commands.month import CreatePlayerMonthLog
from apps.warband.month.models.player_month_log import PlayerMonthLog


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
def handle_log_rival_defeat(*, context: FactionWasDefeated) -> Command | None:
    """
    Says that a rival is out of the game, and that the fight the player just won is what did it.

    Until this line existed the knockout was invisible: the rival's row drops off the rivals list
    because a defeated faction stops getting a month, and that vanishing was the whole of the
    notification. It says who fell and which faction he led, because the causal link between the man
    the player put down and the faction leaving the war is the part he cannot reconstruct - the
    battle report names the prisoner and says nothing about what taking him ended.

    Silent for the player's own faction: his leader falling ends the savegame, and the line about
    that is already written against SavegameEnded. Two lines for the one faction would compete.
    """
    # The instances rather than their ids: Django compares two unsaved rows by identity instead of
    # by a primary key they both lack, so this stays right for a handler called with built factions
    if context.faction == context.player_faction:
        return None

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


@message_registry.register_event(event=MonthlyBuildingMoneyEarned)
def handle_monthly_building_earnings(*, context: MonthlyBuildingMoneyEarned) -> Command:
    return CreatePlayerMonthLog(
        title=f"Buildings earned {context.amount} silver this month.",
        kind=PlayerMonthLog.KindChoices.KIND_BUILDING_INCOME,
        month=context.month,
        faction=context.faction,
    )
