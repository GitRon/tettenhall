from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.skirmish.messages.events.warrior import WarriorImprovedStats, WarriorWasIncapacitated
from apps.warband.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.warrior.handlers.events.skirmish import (
    handle_beating_may_leave_a_mark,
    handle_level_up_earns_a_nickname,
)
from apps.warband.warrior.messages.commands.warrior import AwardEarnedNickname, InflictInjury


def test_handle_level_up_earns_a_nickname_takes_the_month_off_the_fight():
    """
    Nothing in a level-up chain carries a month, and the log line the award ends in needs one.
    """
    warrior = WarriorFactory.build()
    skirmish = SkirmishFactory.build(month=7)

    result = handle_level_up_earns_a_nickname(
        context=WarriorImprovedStats(
            skirmish=skirmish,
            warrior=warrior,
            gained_strength=1,
            gained_dexterity=1,
            gained_max_health=2,
            gained_max_morale=2,
            gained_salary=5,
            new_monthly_salary=55,
        )
    )

    assert result == AwardEarnedNickname(warrior=warrior, month=7)


def test_handle_beating_may_leave_a_mark_carries_the_depth_and_the_month():
    """
    The overkill depth is what scales the roll, and the month comes off the fight the way the award
    above takes it.
    """
    faction = FactionFactory.build()
    warrior = WarriorFactory.build(faction=faction)
    skirmish = SkirmishFactory.build(month=7)

    result = handle_beating_may_leave_a_mark(
        context=WarriorWasIncapacitated(
            skirmish=skirmish,
            warrior=warrior,
            by_warrior=WarriorFactory.build(),
            overkill_health=2,
        )
    )

    assert result == InflictInjury(skirmish=skirmish, warrior=warrior, faction=faction, overkill_health=2, month=7)
