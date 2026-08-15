from apps.faction.tests.factories.faction import FactionFactory
from apps.month.handlers.events.warrior import (
    handle_warrior_deserted_over_unpaid_salary,
    handle_warrior_health_healed,
    handle_warrior_morale_replenished,
)
from apps.month.messages.commands.month import CreatePlayerMonthLog
from apps.skirmish.tests.factories.warrior import WarriorFactory
from apps.warrior.messages.events.warrior import (
    WarriorDesertedOverUnpaidSalary,
    WarriorHealthHealed,
    WarriorMoraleReplenished,
)


def test_handle_warrior_morale_replenished_logs_the_recovery():
    faction = FactionFactory.build()
    warrior = WarriorFactory.build(name="Beorn", faction=faction)

    result = handle_warrior_morale_replenished(
        context=WarriorMoraleReplenished(warrior=warrior, faction=faction, recovered_morale=5, month=3)
    )

    assert result == CreatePlayerMonthLog(
        title="Morale of warrior Beorn was replenished to the maximum.", month=3, faction=faction
    )


def test_handle_warrior_health_healed_logs_the_healed_points():
    faction = FactionFactory.build()
    warrior = WarriorFactory.build(name="Beorn", faction=faction)

    result = handle_warrior_health_healed(
        context=WarriorHealthHealed(warrior=warrior, faction=faction, healed_points=5, month=3)
    )

    assert result == CreatePlayerMonthLog(title="Warrior Beorn healed 5 HP.", month=3, faction=faction)


def test_handle_warrior_deserted_over_unpaid_salary_logs_the_departure():
    """
    The faction comes off the event rather than off the warrior: desertion clears his own FK, so by
    the time this runs there is nothing on him left to log against.
    """
    faction = FactionFactory.build()
    warrior = WarriorFactory.build(name="Oswine", faction=None, savegame=faction.savegame, culture=faction.culture)

    result = handle_warrior_deserted_over_unpaid_salary(
        context=WarriorDesertedOverUnpaidSalary(warrior=warrior, faction=faction, month=3)
    )

    assert result == CreatePlayerMonthLog(title="Oswine left the war band over unpaid wages.", month=3, faction=faction)
