import pytest

from apps.skirmish.handlers.commands.warrior import (
    handle_reduce_morale_of_remaining_warriors,
    handle_reduce_warrior_health,
    handle_warrior_increasing_experience,
    handle_warrior_increasing_morale,
    handle_warrior_is_captured,
    handle_warrior_losing_morale,
)
from apps.skirmish.messages.commands.warrior import (
    CaptureWarrior,
    IncreaseExperience,
    IncreaseMorale,
    ReduceHealth,
    ReduceMorale,
    ReduceMoraleOfRemainingWarriors,
)
from apps.skirmish.messages.events.warrior import (
    WarriorGainedExperience,
    WarriorGainedMorale,
    WarriorHasFled,
    WarriorLostMorale,
    WarriorWasCaptured,
    WarriorWasIncapacitated,
    WarriorWasKilled,
)
from apps.skirmish.models.warrior import Warrior
from apps.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_handle_warrior_is_captured_hands_the_warrior_to_the_victor():
    skirmish = SkirmishFactory()
    captured_warrior = WarriorFactory(faction=skirmish.non_player_faction)

    result = handle_warrior_is_captured(
        context=CaptureWarrior(skirmish=skirmish, warrior=captured_warrior, capturing_faction=skirmish.player_faction)
    )

    assert result == WarriorWasCaptured(
        skirmish=skirmish, warrior=captured_warrior, capturing_faction=skirmish.player_faction
    )
    assert list(skirmish.player_faction.captured_warriors.all()) == [captured_warrior]


@pytest.mark.django_db
def test_handle_warrior_is_captured_takes_the_warrior_out_of_his_faction():
    skirmish = SkirmishFactory()
    captured_warrior = WarriorFactory(faction=skirmish.non_player_faction)

    handle_warrior_is_captured(
        context=CaptureWarrior(skirmish=skirmish, warrior=captured_warrior, capturing_faction=skirmish.player_faction)
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
    second_skirmish = SkirmishFactory(player_faction=skirmish.player_faction)
    captured_warrior = WarriorFactory(faction=skirmish.non_player_faction)
    skirmish.player_faction.captured_warriors.add(captured_warrior)

    result = handle_warrior_is_captured(
        context=CaptureWarrior(
            skirmish=second_skirmish,
            warrior=captured_warrior,
            capturing_faction=second_skirmish.non_player_faction,
        )
    )

    assert result is None
    assert list(second_skirmish.non_player_faction.captured_warriors.all()) == []


@pytest.mark.django_db
def test_handle_reduce_warrior_health_kills_the_warrior():
    skirmish = SkirmishFactory()
    attacker = WarriorFactory(faction=skirmish.player_faction)
    defender = WarriorFactory(faction=skirmish.non_player_faction, current_health=20, max_health=20)

    result = handle_reduce_warrior_health(
        context=ReduceHealth(skirmish=skirmish, warrior=defender, attacker=attacker, lost_health=24)
    )

    assert result == [WarriorWasKilled(skirmish=skirmish, warrior=defender, by_warrior=attacker)]
    defender.refresh_from_db()
    assert defender.condition == Warrior.ConditionChoices.CONDITION_DEAD


@pytest.mark.django_db
def test_handle_reduce_warrior_health_incapacitates_the_warrior():
    skirmish = SkirmishFactory()
    attacker = WarriorFactory(faction=skirmish.player_faction)
    defender = WarriorFactory(faction=skirmish.non_player_faction, current_health=20, max_health=20)

    result = handle_reduce_warrior_health(
        context=ReduceHealth(skirmish=skirmish, warrior=defender, attacker=attacker, lost_health=23)
    )

    assert result == [WarriorWasIncapacitated(skirmish=skirmish, warrior=defender, by_warrior=attacker)]
    defender.refresh_from_db()
    assert defender.condition == Warrior.ConditionChoices.CONDITION_UNCONSCIOUS


@pytest.mark.django_db
def test_handle_reduce_warrior_health_leaves_a_surviving_warrior_healthy():
    skirmish = SkirmishFactory()
    attacker = WarriorFactory(faction=skirmish.player_faction)
    defender = WarriorFactory(faction=skirmish.non_player_faction, current_health=20, max_health=20)

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
        faction=skirmish.player_faction,
        condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS,
        current_morale=20,
        max_morale=20,
    )

    result = handle_warrior_losing_morale(context=ReduceMorale(skirmish=skirmish, warrior=warrior, lost_morale=5))

    assert result == []


@pytest.mark.django_db
def test_handle_warrior_losing_morale_makes_the_warrior_flee_without_morale_left():
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.player_faction, current_morale=5, max_morale=20)

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
    warrior = WarriorFactory(faction=skirmish.player_faction, current_morale=20, max_morale=20)

    result = handle_warrior_losing_morale(context=ReduceMorale(skirmish=skirmish, warrior=warrior, lost_morale=2))

    assert result == [WarriorLostMorale(skirmish=skirmish, warrior=warrior, lost_morale=2)]
    warrior.refresh_from_db()
    assert warrior.current_morale == 18


@pytest.mark.django_db
def test_handle_warrior_losing_morale_stays_silent_without_a_morale_loss():
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.player_faction, current_morale=20, max_morale=20)

    result = handle_warrior_losing_morale(context=ReduceMorale(skirmish=skirmish, warrior=warrior, lost_morale=0))

    assert result == []


@pytest.mark.django_db
def test_handle_reduce_morale_of_remaining_warriors_hits_the_comrades_of_a_player_warrior():
    skirmish = SkirmishFactory()
    fleeing_warrior = WarriorFactory(faction=skirmish.player_faction, max_morale=20)
    comrade = WarriorFactory(faction=skirmish.player_faction)
    skirmish.player_warriors.add(fleeing_warrior, comrade)

    result = handle_reduce_morale_of_remaining_warriors(
        context=ReduceMoraleOfRemainingWarriors(skirmish=skirmish, warrior=fleeing_warrior)
    )

    assert result == [ReduceMorale(skirmish=skirmish, warrior=comrade, lost_morale=2)]


@pytest.mark.django_db
def test_handle_reduce_morale_of_remaining_warriors_hits_the_comrades_of_an_enemy_warrior():
    skirmish = SkirmishFactory()
    incapacitated_warrior = WarriorFactory(faction=skirmish.non_player_faction, max_morale=20)
    comrade = WarriorFactory(faction=skirmish.non_player_faction)
    skirmish.non_player_warriors.add(incapacitated_warrior, comrade)

    result = handle_reduce_morale_of_remaining_warriors(
        context=ReduceMoraleOfRemainingWarriors(skirmish=skirmish, warrior=incapacitated_warrior)
    )

    assert result == [ReduceMorale(skirmish=skirmish, warrior=comrade, lost_morale=2)]


@pytest.mark.django_db
def test_handle_reduce_morale_of_remaining_warriors_skips_the_warrior_himself():
    skirmish = SkirmishFactory()
    killed_warrior = WarriorFactory(faction=skirmish.player_faction, max_morale=20)
    skirmish.player_warriors.add(killed_warrior)

    result = handle_reduce_morale_of_remaining_warriors(
        context=ReduceMoraleOfRemainingWarriors(skirmish=skirmish, warrior=killed_warrior)
    )

    assert result == []


@pytest.mark.django_db
def test_handle_warrior_increasing_morale_adds_the_gained_points():
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.player_faction, current_morale=10, max_morale=20)

    result = handle_warrior_increasing_morale(
        context=IncreaseMorale(skirmish=skirmish, warrior=warrior, increased_morale=5)
    )

    assert result == WarriorGainedMorale(skirmish=skirmish, warrior=warrior, gained_morale=5)
    warrior.refresh_from_db()
    assert warrior.current_morale == 15


@pytest.mark.django_db
def test_handle_warrior_increasing_experience_adds_the_gained_points():
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.player_faction, experience=100)

    result = handle_warrior_increasing_experience(
        context=IncreaseExperience(skirmish=skirmish, warrior=warrior, increased_experience=25)
    )

    assert result == WarriorGainedExperience(skirmish=skirmish, warrior=warrior, gained_experience=25)
    warrior.refresh_from_db()
    assert warrior.experience == 125
