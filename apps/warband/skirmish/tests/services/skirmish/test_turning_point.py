import pytest

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.skirmish.choices.turning_point import TurningPointChoices
from apps.warband.skirmish.domain.turning_point import TurningPointFinding
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.skirmish.services.skirmish.turning_point import TurningPointService
from apps.warband.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_process_has_nothing_to_say_about_a_fight_the_player_has_no_side_in():
    skirmish = SkirmishFactory()
    bystander = FactionFactory(savegame=skirmish.attacking_faction.savegame)

    result = TurningPointService(skirmish=skirmish, fielded_warriors=[], player_faction=bystander).process()

    assert result is None


@pytest.mark.django_db
def test_process_finds_nothing_in_a_quiet_round():
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.attacking_faction)
    skirmish.attacking_warriors.add(warrior)

    result = TurningPointService(
        skirmish=skirmish, fielded_warriors=[warrior], player_faction=skirmish.attacking_faction
    ).process()

    assert result == TurningPointFinding(
        turning_point=None, warriors=[], attacking_leader_in_trouble=False, defending_leader_in_trouble=False
    )


@pytest.mark.django_db
def test_process_names_every_man_the_round_put_down_in_one_stop():
    skirmish = SkirmishFactory()
    knocked_out = WarriorFactory(
        faction=skirmish.attacking_faction, condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS
    )
    fled = WarriorFactory(faction=skirmish.attacking_faction, condition=Warrior.ConditionChoices.CONDITION_FLEEING)
    skirmish.attacking_warriors.add(knocked_out, fled)

    result = TurningPointService(
        skirmish=skirmish, fielded_warriors=[knocked_out, fled], player_faction=skirmish.attacking_faction
    ).process()

    assert result.turning_point == TurningPointChoices.MAN_DOWN
    assert result.warriors == [knocked_out, fled]


@pytest.mark.django_db
def test_process_does_not_count_a_man_who_was_already_down():
    """
    Only the men who went into the round count. One who lay there before it is old news.
    """
    skirmish = SkirmishFactory()
    long_fallen = WarriorFactory(faction=skirmish.attacking_faction, condition=Warrior.ConditionChoices.CONDITION_DEAD)
    skirmish.attacking_warriors.add(long_fallen)

    result = TurningPointService(
        skirmish=skirmish, fielded_warriors=[], player_faction=skirmish.attacking_faction
    ).process()

    assert result.turning_point is None


@pytest.mark.django_db
def test_process_does_not_stop_for_the_enemy_going_down():
    skirmish = SkirmishFactory()
    enemy = WarriorFactory(faction=skirmish.defending_faction, condition=Warrior.ConditionChoices.CONDITION_DEAD)
    skirmish.defending_warriors.add(enemy)

    result = TurningPointService(
        skirmish=skirmish, fielded_warriors=[enemy], player_faction=skirmish.attacking_faction
    ).process()

    assert result.turning_point is None


@pytest.mark.django_db
def test_process_warns_of_the_players_leader_in_trouble():
    skirmish = SkirmishFactory()
    leader = WarriorFactory(faction=skirmish.defending_faction, current_health=9, max_health=20)
    skirmish.defending_faction.leader = leader
    skirmish.defending_faction.save()
    skirmish.defending_warriors.add(leader)

    result = TurningPointService(
        skirmish=skirmish, fielded_warriors=[leader], player_faction=skirmish.defending_faction
    ).process()

    assert result == TurningPointFinding(
        turning_point=TurningPointChoices.LEADER_THREATENED,
        warriors=[],
        attacking_leader_in_trouble=False,
        defending_leader_in_trouble=True,
    )


@pytest.mark.django_db
def test_process_warns_of_the_players_leader_only_once():
    skirmish = SkirmishFactory(attacking_leader_was_in_trouble=True)
    leader = WarriorFactory(faction=skirmish.attacking_faction, current_health=5, max_health=20)
    skirmish.attacking_faction.leader = leader
    skirmish.attacking_faction.save()
    skirmish.attacking_warriors.add(leader)

    result = TurningPointService(
        skirmish=skirmish, fielded_warriors=[leader], player_faction=skirmish.attacking_faction
    ).process()

    assert result.turning_point is None


@pytest.mark.django_db
def test_process_reports_a_fallen_leader_as_a_man_down():
    """
    A leader who went down this round is past being pulled back, so he is not "threatened".
    """
    skirmish = SkirmishFactory()
    leader = WarriorFactory(
        faction=skirmish.attacking_faction,
        current_health=0,
        max_health=20,
        condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS,
    )
    skirmish.attacking_faction.leader = leader
    skirmish.attacking_faction.save()
    skirmish.attacking_warriors.add(leader)

    result = TurningPointService(
        skirmish=skirmish, fielded_warriors=[leader], player_faction=skirmish.attacking_faction
    ).process()

    assert result.turning_point == TurningPointChoices.MAN_DOWN
    assert result.attacking_leader_in_trouble is False


@pytest.mark.django_db
def test_process_points_out_the_enemy_leader_exposed():
    skirmish = SkirmishFactory()
    enemy_leader = WarriorFactory(faction=skirmish.defending_faction, current_health=9, max_health=20)
    skirmish.defending_faction.leader = enemy_leader
    skirmish.defending_faction.save()
    skirmish.defending_warriors.add(enemy_leader)

    result = TurningPointService(
        skirmish=skirmish, fielded_warriors=[enemy_leader], player_faction=skirmish.attacking_faction
    ).process()

    assert result.turning_point == TurningPointChoices.ENEMY_LEADER_EXPOSED


@pytest.mark.django_db
def test_process_ignores_a_leader_who_is_not_in_the_fight():
    """
    A faction's leader who stayed home is in no danger from this fight, whatever his health.
    """
    skirmish = SkirmishFactory()
    home_leader = WarriorFactory(faction=skirmish.defending_faction, current_health=1, max_health=20)
    skirmish.defending_faction.leader = home_leader
    skirmish.defending_faction.save()

    result = TurningPointService(
        skirmish=skirmish, fielded_warriors=[], player_faction=skirmish.attacking_faction
    ).process()

    assert result.defending_leader_in_trouble is False


@pytest.mark.django_db
def test_process_spends_an_outranked_turning_point_all_the_same():
    """
    The player's leader and the enemy's both fell below half in one round: one stop, both seen.
    """
    skirmish = SkirmishFactory()
    leader = WarriorFactory(faction=skirmish.attacking_faction, current_health=9, max_health=20)
    enemy_leader = WarriorFactory(faction=skirmish.defending_faction, current_health=9, max_health=20)
    skirmish.attacking_faction.leader = leader
    skirmish.attacking_faction.save()
    skirmish.defending_faction.leader = enemy_leader
    skirmish.defending_faction.save()
    skirmish.attacking_warriors.add(leader)
    skirmish.defending_warriors.add(enemy_leader)

    result = TurningPointService(
        skirmish=skirmish, fielded_warriors=[leader, enemy_leader], player_faction=skirmish.attacking_faction
    ).process()

    assert result == TurningPointFinding(
        turning_point=TurningPointChoices.LEADER_THREATENED,
        warriors=[],
        attacking_leader_in_trouble=True,
        defending_leader_in_trouble=True,
    )
