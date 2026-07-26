import pytest

from apps.skirmish.handlers.commands.warrior import (
    handle_reduce_warrior_health,
    handle_warrior_losing_morale,
)
from apps.skirmish.messages.commands.warrior import ReduceHealth, ReduceMorale
from apps.skirmish.messages.events.warrior import (
    WarriorHasFled,
    WarriorLostMorale,
    WarriorWasIncapacitated,
    WarriorWasKilled,
)
from apps.skirmish.models.warrior import Warrior
from apps.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.skirmish.tests.factories.warrior import WarriorFactory


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

    assert result == [
        WarriorHasFled(skirmish=skirmish, warrior=warrior),
        WarriorLostMorale(skirmish=skirmish, warrior=warrior, lost_morale=5),
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
