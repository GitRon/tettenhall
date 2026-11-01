from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.warrior.choices.nickname import NicknameStateChoices
from apps.warband.warrior.choices.warrior_milestone import JoinedWayChoices, MilestoneKindChoices
from apps.warband.warrior.handlers.events.warrior import (
    handle_raised_ceiling_earns_a_nickname,
    handle_record_a_change_in_a_man,
    handle_record_a_founding_leader,
    handle_record_a_naming,
)
from apps.warband.warrior.messages.commands.warrior import AwardEarnedNickname, RecordWarriorMilestone
from apps.warband.warrior.messages.events.warrior import (
    NewLeaderWarriorCreated,
    WarriorEarnedNickname,
    WarriorGainedTrait,
    WarriorMaxMoraleChanged,
)


def test_handle_raised_ceiling_earns_a_nickname_asks_after_a_relic():
    faction = FactionFactory.build()
    warrior = WarriorFactory.build(faction=faction)

    result = handle_raised_ceiling_earns_a_nickname(
        context=WarriorMaxMoraleChanged(warrior=warrior, faction=faction, changed_max_morale=4, month=3)
    )

    assert result == AwardEarnedNickname(warrior=warrior, month=3)


def test_handle_raised_ceiling_earns_a_nickname_stays_out_of_a_cut():
    """
    The Devil at the ford, carrying the same share the relic adds. A man whose nerve has just been taken
    off him may be at the bottom of what his kind rolls, and naming him for that is the rename downward
    the whole story exists to stop.
    """
    faction = FactionFactory.build()
    warrior = WarriorFactory.build(faction=faction)

    result = handle_raised_ceiling_earns_a_nickname(
        context=WarriorMaxMoraleChanged(warrior=warrior, faction=faction, changed_max_morale=-4, month=3)
    )

    assert result is None


def test_handle_raised_ceiling_earns_a_nickname_stays_out_of_a_cut_that_took_nothing():
    """
    A cut is truncated against what the man has, so a levy with four morale loses none of it - and a
    ceiling that did not move is not a gain.
    """
    faction = FactionFactory.build()
    warrior = WarriorFactory.build(faction=faction)

    result = handle_raised_ceiling_earns_a_nickname(
        context=WarriorMaxMoraleChanged(warrior=warrior, faction=faction, changed_max_morale=0, month=3)
    )

    assert result is None


def test_handle_record_a_founding_leader_says_he_led_it_from_its_first_day():
    faction = FactionFactory.build()
    leader = WarriorFactory.build(faction=faction)

    result = handle_record_a_founding_leader(context=NewLeaderWarriorCreated(warrior=leader, faction=faction, month=1))

    assert result == RecordWarriorMilestone(
        warrior=leader,
        faction=faction,
        kind=MilestoneKindChoices.JOINED,
        month=1,
        joined_way=JoinedWayChoices.FOUNDED,
    )


def test_handle_record_a_naming_keeps_the_deed_and_the_man_it_was_done_to():
    faction = FactionFactory.build()
    warrior = WarriorFactory.build(faction=faction)
    giant = WarriorFactory.build()
    skirmish = SkirmishFactory.build()

    result = handle_record_a_naming(
        context=WarriorEarnedNickname(
            warrior=warrior,
            faction=faction,
            nickname="the Giantbane",
            nickname_state=NicknameStateChoices.GIANTBANE,
            previous_nickname=None,
            month=4,
            skirmish=skirmish,
            fallen_warrior=giant,
        )
    )

    assert result == RecordWarriorMilestone(
        warrior=warrior,
        faction=faction,
        kind=MilestoneKindChoices.NAMED,
        month=4,
        skirmish=skirmish,
        other_warrior=giant,
        nickname_state=NicknameStateChoices.GIANTBANE,
    )


def test_handle_record_a_change_in_a_man_keeps_the_fight_and_not_the_trait():
    faction = FactionFactory.build()
    warrior = WarriorFactory.build(faction=faction)
    skirmish = SkirmishFactory.build()

    result = handle_record_a_change_in_a_man(
        context=WarriorGainedTrait(skirmish=skirmish, warrior=warrior, faction=faction, month=6)
    )

    assert result == RecordWarriorMilestone(
        warrior=warrior, faction=faction, kind=MilestoneKindChoices.CHANGED, month=6, skirmish=skirmish
    )
