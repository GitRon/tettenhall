from queuebie import message_registry
from queuebie.messages import Command

from apps.warband.month.messages.commands.month import CreatePlayerMonthLog
from apps.warband.month.models.player_month_log import PlayerMonthLog
from apps.warband.warrior.messages.events.warrior import (
    WarriorEarnedNickname,
    WarriorHealthHealed,
    WarriorLostMoraleOverUnpaidSalary,
    WarriorMoraleReplenished,
    WarriorWalkedOutOverUnpaidSalary,
    WarriorWasDismissed,
)


@message_registry.register_event(event=WarriorMoraleReplenished)
def handle_warrior_morale_replenished(*, context: WarriorMoraleReplenished) -> Command:
    # The faction comes off the event, not off the warrior. An event handler runs behind the database
    # blocker, and "warrior.faction" is only free when something upstream happened to leave the
    # relation cached - a "refresh_from_db" in the command handler that raised this drops it, and the
    # read that follows is a query in a place that may not make one. The event carries what is needed.
    return CreatePlayerMonthLog(
        title=f"Morale of warrior {context.warrior} was replenished to the maximum.",
        kind=PlayerMonthLog.KindChoices.KIND_MORALE_RECOVERED,
        month=context.month,
        faction=context.faction,
    )


@message_registry.register_event(event=WarriorHealthHealed)
def handle_warrior_health_healed(*, context: WarriorHealthHealed) -> Command:
    return CreatePlayerMonthLog(
        title=f"Warrior {context.warrior} healed {context.healed_points} HP.",
        kind=PlayerMonthLog.KindChoices.KIND_WOUNDS_HEALED,
        month=context.month,
        faction=context.faction,
    )


@message_registry.register_event(event=WarriorEarnedNickname)
def handle_warrior_earned_nickname(*, context: WarriorEarnedNickname) -> Command:
    """
    The one line that tells the player his man has a name now.

    A name nobody is told about is a name nobody uses, and the epithet was silently moving before this
    existed - so the moment it is settled is the moment to say so. It is said once per man for the
    whole savegame, which is what keeps it off the upkeep tally.
    """
    return CreatePlayerMonthLog(
        title=f"{context.warrior} is known as {context.nickname} from now on.",
        kind=PlayerMonthLog.KindChoices.KIND_NICKNAME_EARNED,
        month=context.month,
        faction=context.faction,
    )


@message_registry.register_event(event=WarriorLostMoraleOverUnpaidSalary)
def handle_warrior_lost_morale_over_unpaid_salary(*, context: WarriorLostMoraleOverUnpaidSalary) -> Command:
    """
    The quieter half of a month without wages, beside the walk-out that is the loud one.

    A line per man, which the upkeep tally turns back into one sentence - the reason this is worth
    reporting at all is the count, and low morale is what routs a warrior in the next fight.
    """
    return CreatePlayerMonthLog(
        title=f"{context.warrior} lost {context.lost_morale} morale over unpaid wages.",
        kind=PlayerMonthLog.KindChoices.KIND_MORALE_LOST_UNPAID,
        month=context.month,
        faction=context.faction,
    )


@message_registry.register_event(event=WarriorWalkedOutOverUnpaidSalary)
def handle_warrior_walked_out_over_unpaid_salary(*, context: WarriorWalkedOutOverUnpaidSalary) -> Command:
    # The faction comes off the event rather than off the warrior: walking out clears his own FK, so
    # by the time this runs there is nothing on him left to log against
    return CreatePlayerMonthLog(
        title=f"{context.warrior} left the war band over unpaid wages.",
        kind=PlayerMonthLog.KindChoices.KIND_WARRIOR_WALKED_OUT,
        month=context.month,
        faction=context.faction,
    )


@message_registry.register_event(event=WarriorWasDismissed)
def handle_warrior_was_dismissed(*, context: WarriorWasDismissed) -> Command:
    # The faction comes off the event rather than off the warrior, for the same reason the walk-out
    # line does: being sent away clears his own FK, so there is nothing left on him to log against
    return CreatePlayerMonthLog(
        title=f"{context.warrior} was sent away for {context.severance_pay} silver.",
        kind=PlayerMonthLog.KindChoices.KIND_WARRIOR_DISMISSED,
        month=context.month,
        faction=context.faction,
    )
