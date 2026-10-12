from apps.warband.skirmish.messages.events.skirmish import FortificationFell, SkirmishFinished
from apps.warband.skirmish.messages.events.warrior import (
    WarriorImprovedStats,
    WarriorWasIncapacitated,
    WarriorWasKilled,
)
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.warrior.choices.nickname import NicknameStateChoices
from apps.warband.warrior.handlers.events.skirmish import (
    handle_a_killing_blow_may_name_the_killer,
    handle_beating_may_leave_a_mark,
    handle_bringing_down_the_walls_earns_a_nickname,
    handle_felling_a_giant_earns_a_nickname,
    handle_fight_may_change_a_man,
    handle_fight_may_name_a_man,
    handle_level_up_earns_a_nickname,
)
from apps.warband.warrior.messages.commands.warrior import (
    AwardDeedNickname,
    AwardEarnedNickname,
    EarnDeedsInSkirmish,
    EarnTraitsInSkirmish,
    InflictInjury,
)
from apps.warband.warrior.services.nickname import GIANTBANE_LEVEL_GAP

# The experience that puts a man exactly the gap above a fresh one, and one level short of it
GIANT_EXPERIENCE = (GIANTBANE_LEVEL_GAP**2) * Warrior.XP_LEVEL_BASE
ONE_SHORT_EXPERIENCE = ((GIANTBANE_LEVEL_GAP - 1) ** 2) * Warrior.XP_LEVEL_BASE


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

    Nothing else rides along. His faction is read in the command handler, because reaching for it
    here is a query and this is an event handler - which no unit test can show, since calling a
    handler directly leaves strict mode's blocker behind. The flow test in
    "apps/warband/skirmish/tests/test_flows.py" is what holds that.
    """
    warrior = WarriorFactory.build()
    skirmish = SkirmishFactory.build(month=7)

    result = handle_beating_may_leave_a_mark(
        context=WarriorWasIncapacitated(
            skirmish=skirmish,
            warrior=warrior,
            by_warrior=WarriorFactory.build(),
            overkill_health=2,
        )
    )

    assert result == InflictInjury(skirmish=skirmish, warrior=warrior, overkill_health=2, month=7)


def test_handle_fight_may_change_a_man_relays_the_fight_and_its_month():
    skirmish = SkirmishFactory.build(month=4)

    result = handle_fight_may_change_a_man(
        context=SkirmishFinished(
            skirmish=skirmish,
            incapacitated_warriors=[],
            defeated_unconscious_warriors=[],
            victorious_healthy_warriors=[],
            month=4,
        )
    )

    assert result == EarnTraitsInSkirmish(skirmish=skirmish, month=4)


def test_handle_a_killing_blow_may_name_the_killer_for_a_leader():
    """
    The killer, not the fallen: the name is for the blow, and the month comes off the fight the way
    the level-up award takes it.
    """
    leader = WarriorFactory.build()
    killer = WarriorFactory.build()
    skirmish = SkirmishFactory.build(month=7)

    result = handle_a_killing_blow_may_name_the_killer(
        context=WarriorWasKilled(skirmish=skirmish, warrior=leader, by_warrior=killer, fell_as_a_leader=True)
    )

    assert result == AwardDeedNickname(warrior=killer, nickname_state=NicknameStateChoices.LORD_SLAYER, month=7)


def test_handle_a_killing_blow_may_name_the_killer_for_a_leader_far_above_him():
    """
    One blow can be both deeds. The leader is the one named: deciding it here rather than queueing two
    awards keeps the answer off the order the handlers happen to be registered in.
    """
    leader = WarriorFactory.build(experience=GIANT_EXPERIENCE)
    killer = WarriorFactory.build(experience=0)
    skirmish = SkirmishFactory.build(month=7)

    result = handle_a_killing_blow_may_name_the_killer(
        context=WarriorWasKilled(skirmish=skirmish, warrior=leader, by_warrior=killer, fell_as_a_leader=True)
    )

    assert result == AwardDeedNickname(warrior=killer, nickname_state=NicknameStateChoices.LORD_SLAYER, month=7)


def test_handle_a_killing_blow_may_name_the_killer_for_a_giant():
    giant = WarriorFactory.build(experience=GIANT_EXPERIENCE)
    killer = WarriorFactory.build(experience=0)
    skirmish = SkirmishFactory.build(month=7)

    result = handle_a_killing_blow_may_name_the_killer(
        context=WarriorWasKilled(skirmish=skirmish, warrior=giant, by_warrior=killer)
    )

    assert result == AwardDeedNickname(warrior=killer, nickname_state=NicknameStateChoices.GIANTBANE, month=7)


def test_handle_a_killing_blow_may_name_the_killer_for_an_ordinary_death():
    """
    One level short of the gap: an ordinary man killed by a slightly greener one is no deed.
    """
    result = handle_a_killing_blow_may_name_the_killer(
        context=WarriorWasKilled(
            skirmish=SkirmishFactory.build(),
            warrior=WarriorFactory.build(experience=ONE_SHORT_EXPERIENCE),
            by_warrior=WarriorFactory.build(experience=0),
        )
    )

    assert result is None


def test_handle_felling_a_giant_earns_a_nickname_names_the_man_who_felled_him():
    giant = WarriorFactory.build(experience=GIANT_EXPERIENCE)
    striker = WarriorFactory.build(experience=0)
    skirmish = SkirmishFactory.build(month=7)

    result = handle_felling_a_giant_earns_a_nickname(
        context=WarriorWasIncapacitated(skirmish=skirmish, warrior=giant, by_warrior=striker, overkill_health=0)
    )

    assert result == AwardDeedNickname(warrior=striker, nickname_state=NicknameStateChoices.GIANTBANE, month=7)


def test_handle_felling_a_giant_earns_a_nickname_for_a_man_within_reach():
    result = handle_felling_a_giant_earns_a_nickname(
        context=WarriorWasIncapacitated(
            skirmish=SkirmishFactory.build(),
            warrior=WarriorFactory.build(experience=ONE_SHORT_EXPERIENCE),
            by_warrior=WarriorFactory.build(experience=0),
            overkill_health=0,
        )
    )

    assert result is None


def test_handle_bringing_down_the_walls_earns_a_nickname_names_the_last_swing():
    warrior = WarriorFactory.build()
    skirmish = SkirmishFactory.build(month=7)

    result = handle_bringing_down_the_walls_earns_a_nickname(
        context=FortificationFell(skirmish=skirmish, round_number=3, warrior=warrior)
    )

    assert result == AwardDeedNickname(warrior=warrior, nickname_state=NicknameStateChoices.WALLBREAKER, month=7)


def test_handle_fight_may_name_a_man_relays_the_fight_and_its_month():
    skirmish = SkirmishFactory.build()

    result = handle_fight_may_name_a_man(
        context=SkirmishFinished(
            skirmish=skirmish,
            incapacitated_warriors=[],
            defeated_unconscious_warriors=[],
            victorious_healthy_warriors=[],
            month=7,
        )
    )

    assert result == EarnDeedsInSkirmish(skirmish=skirmish, month=7)
