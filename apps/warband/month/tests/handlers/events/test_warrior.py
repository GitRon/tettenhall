from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.month.handlers.events.warrior import (
    handle_warrior_earned_nickname,
    handle_warrior_health_healed,
    handle_warrior_lost_morale_over_unpaid_salary,
    handle_warrior_morale_replenished,
    handle_warrior_walked_out_over_unpaid_salary,
    handle_warrior_was_dismissed,
)
from apps.warband.month.messages.commands.month import CreatePlayerMonthLog
from apps.warband.month.models.player_month_log import PlayerMonthLog
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.warrior.messages.events.warrior import (
    WarriorEarnedNickname,
    WarriorHealthHealed,
    WarriorLostMoraleOverUnpaidSalary,
    WarriorMoraleReplenished,
    WarriorWalkedOutOverUnpaidSalary,
    WarriorWasDismissed,
)


def test_handle_warrior_morale_replenished_logs_the_recovery():
    faction = FactionFactory.build()
    warrior = WarriorFactory.build(name="Beorn", faction=faction)

    result = handle_warrior_morale_replenished(
        context=WarriorMoraleReplenished(warrior=warrior, faction=faction, recovered_morale=5, month=3)
    )

    assert result == CreatePlayerMonthLog(
        title="Morale of warrior Beorn was replenished to the maximum.",
        kind=PlayerMonthLog.KindChoices.KIND_MORALE_RECOVERED,
        month=3,
        faction=faction,
    )


def test_handle_warrior_health_healed_logs_the_healed_points():
    faction = FactionFactory.build()
    warrior = WarriorFactory.build(name="Beorn", faction=faction)

    result = handle_warrior_health_healed(
        context=WarriorHealthHealed(warrior=warrior, faction=faction, healed_points=5, month=3)
    )

    assert result == CreatePlayerMonthLog(
        title="Warrior Beorn healed 5 HP.",
        kind=PlayerMonthLog.KindChoices.KIND_WOUNDS_HEALED,
        month=3,
        faction=faction,
    )


def test_handle_warrior_lost_morale_over_unpaid_salary_logs_what_it_cost_him():
    faction = FactionFactory.build()
    warrior = WarriorFactory.build(name="Beorn", faction=faction)

    result = handle_warrior_lost_morale_over_unpaid_salary(
        context=WarriorLostMoraleOverUnpaidSalary(warrior=warrior, faction=faction, lost_morale=3, month=3)
    )

    assert result == CreatePlayerMonthLog(
        title="Beorn lost 3 morale over unpaid wages.",
        kind=PlayerMonthLog.KindChoices.KIND_MORALE_LOST_UNPAID,
        month=3,
        faction=faction,
    )


def test_handle_warrior_walked_out_over_unpaid_salary_logs_the_departure():
    """
    The faction comes off the event rather than off the warrior: walking out clears his own FK, so by
    the time this runs there is nothing on him left to log against.
    """
    faction = FactionFactory.build()
    warrior = WarriorFactory.build(name="Oswine", faction=None, savegame=faction.savegame, culture=faction.culture)

    result = handle_warrior_walked_out_over_unpaid_salary(
        context=WarriorWalkedOutOverUnpaidSalary(warrior=warrior, faction=faction, savegame=faction.savegame, month=3)
    )

    assert result == CreatePlayerMonthLog(
        title="Oswine left the war band over unpaid wages.",
        kind=PlayerMonthLog.KindChoices.KIND_WARRIOR_WALKED_OUT,
        month=3,
        faction=faction,
    )


def test_handle_warrior_was_dismissed_logs_what_letting_him_go_cost():
    """
    The faction comes off the event rather than off the warrior, the way the walk-out line does:
    being sent away clears his own FK, so there is nothing left on him to log against.
    """
    faction = FactionFactory.build()
    warrior = WarriorFactory.build(name="Cuthbert", faction=None, savegame=faction.savegame, culture=faction.culture)

    result = handle_warrior_was_dismissed(
        context=WarriorWasDismissed(
            warrior=warrior, faction=faction, savegame=faction.savegame, severance_pay=120, month=3
        )
    )

    assert result == CreatePlayerMonthLog(
        title="Cuthbert was sent away for 120 silver.",
        kind=PlayerMonthLog.KindChoices.KIND_WARRIOR_DISMISSED,
        month=3,
        faction=faction,
    )


def test_handle_warrior_earned_nickname_logs_what_he_is_called_now():
    """
    The epithet comes off the event rather than off the warrior: what the player is told is the name,
    and resolving it here would be a second place the wording is decided.
    """
    faction = FactionFactory.build()
    warrior = WarriorFactory.build(name="Beorn", faction=faction)

    result = handle_warrior_earned_nickname(
        context=WarriorEarnedNickname(warrior=warrior, faction=faction, nickname="the Bold", month=3)
    )

    assert result == CreatePlayerMonthLog(
        title="Beorn is known as the Bold from now on.",
        kind=PlayerMonthLog.KindChoices.KIND_NICKNAME_EARNED,
        month=3,
        faction=faction,
    )
