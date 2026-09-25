import pytest

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.skirmish.choices.skirmish_action import SkirmishActionChoices
from apps.warband.skirmish.handlers.commands.warrior import (
    handle_increase_warrior_stats_on_level_up,
    handle_leader_rallies_remaining_warriors,
    handle_reduce_morale_of_remaining_warriors,
    handle_reduce_warrior_health,
    handle_store_last_used_skirmish_action,
    handle_warrior_increasing_experience,
    handle_warrior_increasing_morale,
    handle_warrior_is_captured,
    handle_warrior_losing_morale,
    handle_warrior_withdraws_from_skirmish,
)
from apps.warband.skirmish.messages.commands.warrior import (
    CaptureWarrior,
    IncreaseExperience,
    IncreaseMorale,
    IncreaseWarriorStatsOnLevelUp,
    RallyRemainingWarriors,
    ReduceHealth,
    ReduceMorale,
    ReduceMoraleOfRemainingWarriors,
    StoreLastUsedSkirmishAction,
    WithdrawFromSkirmish,
)
from apps.warband.skirmish.messages.events.warrior import (
    LastUsedSkirmishActionStored,
    LeaderRallied,
    WarriorGainedExperience,
    WarriorGainedLevel,
    WarriorGainedMorale,
    WarriorHasFled,
    WarriorImprovedStats,
    WarriorLostMorale,
    WarriorSawComradeFall,
    WarriorWasCaptured,
    WarriorWasIncapacitated,
    WarriorWasKilled,
    WarriorWasRallied,
)
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_handle_warrior_is_captured_hands_the_warrior_to_the_victor():
    skirmish = SkirmishFactory()
    captured_warrior = WarriorFactory(faction=skirmish.defending_faction)

    result = handle_warrior_is_captured(
        context=CaptureWarrior(
            skirmish=skirmish, warrior=captured_warrior, capturing_faction=skirmish.attacking_faction
        )
    )

    assert result == WarriorWasCaptured(
        skirmish=skirmish, warrior=captured_warrior, capturing_faction=skirmish.attacking_faction
    )
    assert list(skirmish.attacking_faction.captured_warriors.all()) == [captured_warrior]


@pytest.mark.django_db
def test_handle_warrior_is_captured_without_a_skirmish():
    """
    An occupation seizes a leader where he stands, with no fight to have taken him off the field of.
    """
    occupying_faction = FactionFactory()
    faction = FactionFactory(savegame=occupying_faction.savegame)
    leader = WarriorFactory(faction=faction)

    result = handle_warrior_is_captured(
        context=CaptureWarrior(skirmish=None, warrior=leader, capturing_faction=occupying_faction)
    )

    assert result == WarriorWasCaptured(skirmish=None, warrior=leader, capturing_faction=occupying_faction)
    assert list(occupying_faction.captured_warriors.all()) == [leader]


@pytest.mark.django_db
def test_handle_warrior_is_captured_takes_the_warrior_out_of_his_faction():
    skirmish = SkirmishFactory()
    captured_warrior = WarriorFactory(faction=skirmish.defending_faction)

    handle_warrior_is_captured(
        context=CaptureWarrior(
            skirmish=skirmish, warrior=captured_warrior, capturing_faction=skirmish.attacking_faction
        )
    )

    captured_warrior.refresh_from_db()
    assert captured_warrior.faction is None


@pytest.mark.django_db
def test_handle_warrior_is_captured_leaves_an_existing_prisoner_where_he_is():
    """
    A warrior can be on the roster of two unresolved skirmishes, and ending the game decides both in
    one pass - so this runs twice for him. The second captor does not get to take him off the first.
    """
    skirmish = SkirmishFactory()
    second_skirmish = SkirmishFactory(attacking_faction=skirmish.attacking_faction)
    captured_warrior = WarriorFactory(faction=skirmish.defending_faction)
    skirmish.attacking_faction.captured_warriors.add(captured_warrior)

    result = handle_warrior_is_captured(
        context=CaptureWarrior(
            skirmish=second_skirmish,
            warrior=captured_warrior,
            capturing_faction=second_skirmish.defending_faction,
        )
    )

    assert result is None
    assert list(second_skirmish.defending_faction.captured_warriors.all()) == []


@pytest.mark.django_db
def test_handle_reduce_warrior_health_kills_the_warrior():
    skirmish = SkirmishFactory()
    attacker = WarriorFactory(faction=skirmish.attacking_faction)
    defender = WarriorFactory(faction=skirmish.defending_faction, current_health=20, max_health=20)

    result = handle_reduce_warrior_health(
        context=ReduceHealth(skirmish=skirmish, warrior=defender, attacker=attacker, lost_health=24)
    )

    assert result == [WarriorWasKilled(skirmish=skirmish, warrior=defender, by_warrior=attacker)]
    defender.refresh_from_db()
    assert defender.condition == Warrior.ConditionChoices.CONDITION_DEAD


@pytest.mark.django_db
def test_handle_reduce_warrior_health_incapacitates_the_warrior():
    skirmish = SkirmishFactory()
    attacker = WarriorFactory(faction=skirmish.attacking_faction)
    defender = WarriorFactory(faction=skirmish.defending_faction, current_health=20, max_health=20)

    result = handle_reduce_warrior_health(
        context=ReduceHealth(skirmish=skirmish, warrior=defender, attacker=attacker, lost_health=23)
    )

    assert result == [
        WarriorWasIncapacitated(skirmish=skirmish, warrior=defender, by_warrior=attacker, overkill_health=3)
    ]
    defender.refresh_from_db()
    assert defender.condition == Warrior.ConditionChoices.CONDITION_UNCONSCIOUS


@pytest.mark.django_db
def test_handle_reduce_warrior_health_leaves_a_surviving_warrior_healthy():
    skirmish = SkirmishFactory()
    attacker = WarriorFactory(faction=skirmish.attacking_faction)
    defender = WarriorFactory(faction=skirmish.defending_faction, current_health=20, max_health=20)

    result = handle_reduce_warrior_health(
        context=ReduceHealth(skirmish=skirmish, warrior=defender, attacker=attacker, lost_health=5)
    )

    assert result == []
    defender.refresh_from_db()
    assert defender.current_health == 15


@pytest.mark.django_db
def test_handle_warrior_losing_morale_ignores_an_unconscious_warrior():
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(
        faction=skirmish.attacking_faction,
        condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS,
        current_morale=20,
        max_morale=20,
    )

    result = handle_warrior_losing_morale(context=ReduceMorale(skirmish=skirmish, warrior=warrior, lost_morale=5))

    assert result == []


@pytest.mark.django_db
def test_handle_warrior_losing_morale_makes_the_warrior_flee_without_morale_left():
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.attacking_faction, current_morale=5, max_morale=20)

    result = handle_warrior_losing_morale(context=ReduceMorale(skirmish=skirmish, warrior=warrior, lost_morale=5))

    # The loss before the rout: the battle log is written in the order the events arrive
    assert result == [
        WarriorLostMorale(skirmish=skirmish, warrior=warrior, lost_morale=5),
        WarriorHasFled(skirmish=skirmish, warrior=warrior),
    ]
    warrior.refresh_from_db()
    assert warrior.condition == Warrior.ConditionChoices.CONDITION_FLEEING


@pytest.mark.django_db
def test_handle_warrior_losing_morale_keeps_a_warrior_with_morale_left_fighting():
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.attacking_faction, current_morale=20, max_morale=20)

    result = handle_warrior_losing_morale(context=ReduceMorale(skirmish=skirmish, warrior=warrior, lost_morale=2))

    assert result == [WarriorLostMorale(skirmish=skirmish, warrior=warrior, lost_morale=2)]
    warrior.refresh_from_db()
    assert warrior.current_morale == 18


@pytest.mark.django_db
def test_handle_warrior_losing_morale_stays_silent_without_a_morale_loss():
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.attacking_faction, current_morale=20, max_morale=20)

    result = handle_warrior_losing_morale(context=ReduceMorale(skirmish=skirmish, warrior=warrior, lost_morale=0))

    assert result == []


@pytest.mark.django_db
def test_handle_warrior_withdraws_from_skirmish_walks_him_off_and_charges_him():
    warrior = WarriorFactory(current_morale=20, max_morale=20)
    skirmish = SkirmishFactory()

    result = handle_warrior_withdraws_from_skirmish(context=WithdrawFromSkirmish(skirmish=skirmish, warrior=warrior))

    assert result == WarriorHasFled(skirmish=skirmish, warrior=warrior, was_ordered=True)
    warrior.refresh_from_db()
    assert (warrior.current_morale, warrior.max_morale, warrior.condition) == (
        0,
        19,
        Warrior.ConditionChoices.CONDITION_FLEEING,
    )


@pytest.mark.django_db
def test_handle_warrior_withdraws_from_skirmish_ignores_a_warrior_already_out_of_the_fight():
    """
    Reachable rather than defensive: an order to flee is drained after the round's other messages, so a
    comrade falling can rout the man in the meantime. Charging him a second time would price one
    retreat twice.
    """
    warrior = WarriorFactory(current_morale=0, max_morale=20, condition=Warrior.ConditionChoices.CONDITION_FLEEING)
    skirmish = SkirmishFactory()

    result = handle_warrior_withdraws_from_skirmish(context=WithdrawFromSkirmish(skirmish=skirmish, warrior=warrior))

    assert result == []
    warrior.refresh_from_db()
    assert warrior.max_morale == 20


@pytest.mark.django_db
def test_handle_reduce_morale_of_remaining_warriors_names_the_comrades_of_an_attacking_warrior():
    skirmish = SkirmishFactory()
    fallen_warrior = WarriorFactory(faction=skirmish.attacking_faction, max_morale=20)
    comrade = WarriorFactory(faction=skirmish.attacking_faction)
    skirmish.attacking_warriors.add(fallen_warrior, comrade)

    result = handle_reduce_morale_of_remaining_warriors(
        context=ReduceMoraleOfRemainingWarriors(skirmish=skirmish, warrior=fallen_warrior)
    )

    assert result == [WarriorSawComradeFall(skirmish=skirmish, warrior=comrade, fallen_warrior=fallen_warrior)]


@pytest.mark.django_db
def test_handle_reduce_morale_of_remaining_warriors_names_the_comrades_of_a_defending_warrior():
    skirmish = SkirmishFactory()
    fallen_warrior = WarriorFactory(faction=skirmish.defending_faction, max_morale=20)
    comrade = WarriorFactory(faction=skirmish.defending_faction)
    skirmish.defending_warriors.add(fallen_warrior, comrade)

    result = handle_reduce_morale_of_remaining_warriors(
        context=ReduceMoraleOfRemainingWarriors(skirmish=skirmish, warrior=fallen_warrior)
    )

    assert result == [WarriorSawComradeFall(skirmish=skirmish, warrior=comrade, fallen_warrior=fallen_warrior)]


@pytest.mark.django_db
def test_handle_reduce_morale_of_remaining_warriors_leaves_out_the_fallen_man_himself():
    """
    A man cannot witness his own fall, which is part of the fact rather than something the reaction
    has to filter out.
    """
    skirmish = SkirmishFactory()
    fallen_warrior = WarriorFactory(faction=skirmish.attacking_faction, max_morale=20)
    skirmish.attacking_warriors.add(fallen_warrior)

    result = handle_reduce_morale_of_remaining_warriors(
        context=ReduceMoraleOfRemainingWarriors(skirmish=skirmish, warrior=fallen_warrior)
    )

    assert result == []


@pytest.mark.django_db
def test_handle_reduce_morale_of_remaining_warriors_leaves_the_other_side_alone():
    skirmish = SkirmishFactory()
    fallen_warrior = WarriorFactory(faction=skirmish.attacking_faction, max_morale=20)
    skirmish.attacking_warriors.add(fallen_warrior)
    enemy = WarriorFactory(faction=skirmish.defending_faction)
    skirmish.defending_warriors.add(enemy)

    result = handle_reduce_morale_of_remaining_warriors(
        context=ReduceMoraleOfRemainingWarriors(skirmish=skirmish, warrior=fallen_warrior)
    )

    assert result == []


@pytest.mark.django_db
def test_handle_warrior_increasing_morale_adds_the_gained_points():
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.attacking_faction, current_morale=10, max_morale=20)

    result = handle_warrior_increasing_morale(
        context=IncreaseMorale(skirmish=skirmish, warrior=warrior, increased_morale=5)
    )

    assert result == WarriorGainedMorale(skirmish=skirmish, warrior=warrior, gained_morale=5)
    warrior.refresh_from_db()
    assert warrior.current_morale == 15


@pytest.mark.django_db
def test_handle_warrior_increasing_morale_credits_only_what_the_ceiling_let_through():
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.attacking_faction, current_morale=18, max_morale=20)

    result = handle_warrior_increasing_morale(
        context=IncreaseMorale(skirmish=skirmish, warrior=warrior, increased_morale=5)
    )

    assert result == WarriorGainedMorale(skirmish=skirmish, warrior=warrior, gained_morale=2)
    warrior.refresh_from_db()
    assert warrior.current_morale == 20


@pytest.mark.django_db
def test_handle_warrior_increasing_morale_announces_nothing_for_a_man_at_his_ceiling():
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.attacking_faction, current_morale=20, max_morale=20)

    result = handle_warrior_increasing_morale(
        context=IncreaseMorale(skirmish=skirmish, warrior=warrior, increased_morale=2)
    )

    assert result == []


@pytest.mark.django_db
def test_handle_warrior_increasing_morale_passes_the_rally_on():
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.attacking_faction, current_morale=10, max_morale=20)

    result = handle_warrior_increasing_morale(
        context=IncreaseMorale(skirmish=skirmish, warrior=warrior, increased_morale=2, was_rallied=True)
    )

    assert result == WarriorGainedMorale(skirmish=skirmish, warrior=warrior, gained_morale=2, was_rallied=True)


@pytest.mark.django_db
def test_handle_warrior_increasing_morale_refuses_a_man_who_has_left_the_fight():
    """
    Read off the row rather than the instance on the message: the man fled after the order reached him.
    """
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.attacking_faction, current_morale=0, max_morale=20)
    Warrior.objects.filter(id=warrior.id).update(condition=Warrior.ConditionChoices.CONDITION_FLEEING)

    result = handle_warrior_increasing_morale(
        context=IncreaseMorale(skirmish=skirmish, warrior=warrior, increased_morale=2)
    )

    assert result == []
    warrior.refresh_from_db()
    assert warrior.current_morale == 0


def _skirmish_led_by(*, leader_side: str) -> tuple:
    skirmish = SkirmishFactory()
    faction = getattr(skirmish, f"{leader_side}_faction")
    leader = WarriorFactory(faction=faction)
    faction.leader = leader
    faction.save()
    getattr(skirmish, f"{leader_side}_warriors").add(leader)
    return skirmish, faction, leader


@pytest.mark.django_db
def test_handle_leader_rallies_remaining_warriors_reaches_the_healthy_men_of_an_attacking_leader():
    skirmish, faction, leader = _skirmish_led_by(leader_side="attacking")
    comrade = WarriorFactory(faction=faction)
    enemy = WarriorFactory(faction=skirmish.defending_faction)
    skirmish.attacking_warriors.add(comrade)
    skirmish.defending_warriors.add(enemy)

    result = handle_leader_rallies_remaining_warriors(context=RallyRemainingWarriors(skirmish=skirmish, leader=leader))

    assert result == [
        LeaderRallied(skirmish=skirmish, leader=leader, rallied_warriors=[comrade]),
        WarriorWasRallied(skirmish=skirmish, warrior=comrade),
    ]


@pytest.mark.django_db
def test_handle_leader_rallies_remaining_warriors_reaches_the_men_of_a_defending_leader():
    skirmish, faction, leader = _skirmish_led_by(leader_side="defending")
    comrade = WarriorFactory(faction=faction)
    skirmish.defending_warriors.add(comrade)

    result = handle_leader_rallies_remaining_warriors(context=RallyRemainingWarriors(skirmish=skirmish, leader=leader))

    assert result == [
        LeaderRallied(skirmish=skirmish, leader=leader, rallied_warriors=[comrade]),
        WarriorWasRallied(skirmish=skirmish, warrior=comrade),
    ]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "condition",
    [
        Warrior.ConditionChoices.CONDITION_FLEEING,
        Warrior.ConditionChoices.CONDITION_UNCONSCIOUS,
        Warrior.ConditionChoices.CONDITION_DEAD,
    ],
)
def test_handle_leader_rallies_remaining_warriors_skips_men_out_of_the_fight(condition):
    skirmish, faction, leader = _skirmish_led_by(leader_side="attacking")
    gone = WarriorFactory(faction=faction, condition=condition)
    skirmish.attacking_warriors.add(gone)

    result = handle_leader_rallies_remaining_warriors(context=RallyRemainingWarriors(skirmish=skirmish, leader=leader))

    assert result == [LeaderRallied(skirmish=skirmish, leader=leader, rallied_warriors=[])]


@pytest.mark.django_db
def test_handle_leader_rallies_remaining_warriors_gives_no_order_from_a_leader_who_is_down():
    """
    Late-bound like a withdrawal: the row says he is out, whatever the instance on the order says.
    """
    skirmish, faction, leader = _skirmish_led_by(leader_side="attacking")
    skirmish.attacking_warriors.add(WarriorFactory(faction=faction))
    Warrior.objects.filter(id=leader.id).update(condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS)

    result = handle_leader_rallies_remaining_warriors(context=RallyRemainingWarriors(skirmish=skirmish, leader=leader))

    assert result == []


@pytest.mark.django_db
def test_handle_warrior_increasing_experience_adds_the_gained_points():
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.attacking_faction, experience=100)

    result = handle_warrior_increasing_experience(
        context=IncreaseExperience(skirmish=skirmish, warrior=warrior, increased_experience=25)
    )

    assert result == [WarriorGainedExperience(skirmish=skirmish, warrior=warrior, gained_experience=25)]
    warrior.refresh_from_db()
    assert warrior.experience == 125


@pytest.mark.django_db
def test_handle_warrior_increasing_experience_announces_a_crossed_threshold():
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.attacking_faction, experience=90)

    result = handle_warrior_increasing_experience(
        context=IncreaseExperience(skirmish=skirmish, warrior=warrior, increased_experience=25)
    )

    assert result == [
        WarriorGainedExperience(skirmish=skirmish, warrior=warrior, gained_experience=25),
        WarriorGainedLevel(skirmish=skirmish, warrior=warrior, level=2),
    ]


@pytest.mark.django_db
def test_handle_warrior_increasing_experience_announces_both_of_two_crossed_thresholds():
    """
    A gain spanning two thresholds levels the warrior twice, so it has to grow him twice and read as
    two lines in the log. Clamping to a single level-up would quietly swallow the second.
    """
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.attacking_faction, experience=0)

    result = handle_warrior_increasing_experience(
        context=IncreaseExperience(skirmish=skirmish, warrior=warrior, increased_experience=400)
    )

    assert result == [
        WarriorGainedExperience(skirmish=skirmish, warrior=warrior, gained_experience=400),
        WarriorGainedLevel(skirmish=skirmish, warrior=warrior, level=2),
        WarriorGainedLevel(skirmish=skirmish, warrior=warrior, level=3),
    ]


@pytest.mark.django_db
def test_handle_increase_warrior_stats_on_level_up_reports_every_gain():
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(
        faction=skirmish.attacking_faction, strength=10, dexterity=10, max_health=20, max_morale=20, monthly_salary=150
    )

    result = handle_increase_warrior_stats_on_level_up(
        context=IncreaseWarriorStatsOnLevelUp(skirmish=skirmish, warrior=warrior)
    )

    assert result == WarriorImprovedStats(
        skirmish=skirmish,
        warrior=warrior,
        gained_strength=1,
        gained_dexterity=1,
        gained_max_health=2,
        gained_max_morale=2,
        gained_salary=15,
        new_monthly_salary=165,
    )
    warrior.refresh_from_db()
    assert warrior.monthly_salary == 165


@pytest.mark.django_db
def test_handle_store_last_used_skirmish_action_writes_only_the_action():
    """
    The instance on the order was loaded when the round was posted. What the round has done to the man's
    morale since then stays.
    """
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.attacking_faction, current_morale=10, max_morale=20)
    Warrior.objects.filter(id=warrior.id).update(current_morale=12)

    result = handle_store_last_used_skirmish_action(
        context=StoreLastUsedSkirmishAction(
            skirmish=skirmish, warrior=warrior, skirmish_action=SkirmishActionChoices.RALLY
        )
    )

    assert result == LastUsedSkirmishActionStored(
        skirmish=skirmish, warrior=warrior, skirmish_action=SkirmishActionChoices.RALLY
    )
    warrior.refresh_from_db()
    assert (warrior.last_used_skirmish_action, warrior.current_morale) == (SkirmishActionChoices.RALLY, 12)
