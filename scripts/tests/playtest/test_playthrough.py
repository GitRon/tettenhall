import pytest

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.savegame.models.savegame import Savegame
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from scripts.playtest.playthrough import STOP_MONTH_BLOCKED, Standing, _count_successions, play_months, play_savegame
from scripts.playtest.policy import POLICIES, PlayerPolicy
from scripts.playtest.report import GameReport

# Marches on nobody, so a game played with it cannot be lost and runs to whatever cap it is given
NEVER_MARCHES = PlayerPolicy(name="never", margin=1_000)


@pytest.mark.django_db
def test_play_savegame_plays_games_to_their_end(user, queuebie_registry):
    """
    A handful of games played from the new-game form to their end, which is what pins the harness to the
    game: a view sequence it has fallen out of step with shows up as a game that stalls, or as a step that
    no longer fires in any of them.

    A batch rather than one seed, because a single game is decided by its dice - one aggressive game can
    be lost in its first fight and never see a hire or a succession. Which way each game goes is left
    alone on purpose: that is the balance a change is meant to move, and pinning an outcome to a seed would
    fail every balance change for doing its job. The cap only keeps a stall from hanging the suite, well
    past the month an aggressive game is decided in.
    """
    reports = [play_savegame(seed=seed, policy=POLICIES["aggressive"], month_cap=60, user=user) for seed in range(4, 9)]

    step_counts = {
        "drafted": sum(report.drafted for report in reports),
        "sent on quests": sum(report.sent_on_quests for report in reports),
        "hired": sum(report.hired for report in reports),
        "items bought": sum(report.items_bought for report in reports),
        "items equipped": sum(report.items_equipped for report in reports),
        "built": sum(len(report.built) for report in reports),
        "captives recruited": sum(report.captives_recruited for report in reports),
        "fights won": sum(report.fights_won for report in reports),
        "fights lost": sum(report.fights_lost for report in reports),
        "occupations": sum(report.occupations for report in reports),
        "player successions": sum(report.player_successions for report in reports),
    }

    assert {report.outcome for report in reports} <= {"Won", "Lost"}
    assert [step for step, count in step_counts.items() if count == 0] == []


@pytest.mark.django_db
def test_play_savegame_repeats_for_the_same_seed(user, queuebie_registry):
    first = play_savegame(seed=5, policy=POLICIES["even"], month_cap=3, user=user)

    second = play_savegame(seed=5, policy=POLICIES["even"], month_cap=3, user=user)

    assert first.as_dict() == second.as_dict()


@pytest.mark.django_db
def test_play_savegame_stops_at_the_cap(user, queuebie_registry):
    report = play_savegame(seed=1, policy=NEVER_MARCHES, month_cap=2, user=user)

    assert (report.outcome, report.months_played) == ("Running", 2)
    assert len(report.timeline) == 2


@pytest.mark.django_db
def test_play_months_leaves_a_decided_game_alone(player_savegame, rng, report):
    player_savegame.outcome = Savegame.OutcomeChoices.OUTCOME_LOST
    player_savegame.save()

    result = play_months(savegame=player_savegame, policy=NEVER_MARCHES, rng=rng, month_cap=5, report=report)

    assert (result.outcome, result.months_played) == ("Lost", 0)


@pytest.mark.django_db
def test_play_months_ends_with_the_last_town_taken(player_savegame, rng, report, queuebie_registry):
    rival = FactionFactory(savegame=player_savegame)
    rival.leader = WarriorFactory(faction=rival, condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS)
    rival.save()

    result = play_months(savegame=player_savegame, policy=NEVER_MARCHES, rng=rng, month_cap=5, report=report)

    assert (result.outcome, result.months_played) == ("Won", 1)


@pytest.mark.django_db
def test_play_months_stops_on_a_month_it_may_not_finish(player_savegame, rng, report, queuebie_registry):
    """Two rivals are still fighting each other, and the month refuses to turn while they are."""
    SkirmishFactory(attacking_faction__savegame=player_savegame)

    result = play_months(savegame=player_savegame, policy=NEVER_MARCHES, rng=rng, month_cap=5, report=report)

    assert (result.stop_reason, result.months_played) == (STOP_MONTH_BLOCKED, 1)


@pytest.mark.django_db
def test_count_successions_counts_the_players_new_leader(player_savegame, report):
    faction = player_savegame.player_faction
    fallen_leader_id = faction.leader_id
    successor = WarriorFactory(faction=faction)
    faction.leader = successor
    faction.save()

    _count_successions(
        savegame=player_savegame,
        before={
            faction.id: Standing(leader_id=fallen_leader_id, is_defeated=False, roster_ids=frozenset({successor.id}))
        },
        report=report,
    )

    assert (report.player_successions, report.player_leaders_raised) == (1, 0)


@pytest.mark.django_db
def test_count_successions_counts_a_rivals_new_leader(player_savegame, report):
    rival = FactionFactory(savegame=player_savegame)
    fallen_leader = WarriorFactory(faction=rival)
    successor = WarriorFactory(faction=rival)
    rival.leader = successor
    rival.save()
    faction = player_savegame.player_faction

    _count_successions(
        savegame=player_savegame,
        before={
            faction.id: Standing(leader_id=faction.leader_id, is_defeated=False),
            rival.id: Standing(leader_id=fallen_leader.id, is_defeated=False, roster_ids=frozenset({successor.id})),
        },
        report=report,
    )

    assert (report.player_successions, report.rival_successions, report.rival_leaders_raised) == (0, 1, 0)


@pytest.mark.django_db
def test_count_successions_tells_a_leader_raised_from_the_fyrd_apart(player_savegame, report):
    """The new leader was on nobody's roster before the month: the fyrd raised him, nobody succeeded."""
    rival = FactionFactory(savegame=player_savegame)
    fallen_leader = WarriorFactory(faction=rival)
    rival.leader = WarriorFactory(faction=rival)
    rival.save()
    faction = player_savegame.player_faction

    _count_successions(
        savegame=player_savegame,
        before={
            faction.id: Standing(leader_id=faction.leader_id, is_defeated=False),
            rival.id: Standing(leader_id=fallen_leader.id, is_defeated=False, roster_ids=frozenset()),
        },
        report=report,
    )

    assert (report.rival_successions, report.rival_leaders_raised) == (0, 1)


@pytest.mark.django_db
def test_count_successions_tells_the_players_raised_leader_apart(player_savegame, report):
    faction = player_savegame.player_faction
    fallen_leader_id = faction.leader_id
    faction.leader = WarriorFactory(faction=faction)
    faction.save()

    _count_successions(
        savegame=player_savegame,
        before={faction.id: Standing(leader_id=fallen_leader_id, is_defeated=False, roster_ids=frozenset())},
        report=report,
    )

    assert (report.player_successions, report.player_leaders_raised) == (0, 1)


@pytest.mark.django_db
def test_count_successions_records_a_rival_knocked_out(player_savegame, report):
    """A seat left empty by a faction that is finished is a defeat, not a succession."""
    rival = FactionFactory(savegame=player_savegame, is_defeated=True)
    faction = player_savegame.player_faction
    report.months_played = 4

    _count_successions(
        savegame=player_savegame,
        before={
            faction.id: Standing(leader_id=faction.leader_id, is_defeated=False),
            rival.id: Standing(leader_id=WarriorFactory(faction=rival).id, is_defeated=False),
        },
        report=report,
    )

    assert (report.rival_defeat_months, report.rival_successions, report.rival_months_after_first_fall) == (
        [4],
        0,
        [0],
    )


@pytest.mark.django_db
def test_count_successions_measures_a_rival_from_its_first_fall(player_savegame, report):
    """It lost its first leader in month 2 and lasted until month 5: three months after the fall."""
    rival = FactionFactory(savegame=player_savegame, is_defeated=True)
    faction = player_savegame.player_faction
    report.months_played = 5

    _count_successions(
        savegame=player_savegame,
        before={
            faction.id: Standing(leader_id=faction.leader_id, is_defeated=False),
            rival.id: Standing(leader_id=WarriorFactory(faction=rival).id, is_defeated=False, first_fall_month=2),
        },
        report=report,
    )

    assert report.rival_months_after_first_fall == [3]


@pytest.mark.django_db
def test_count_successions_returns_the_standings_now(player_savegame):
    faction = player_savegame.player_faction

    result = _count_successions(
        savegame=player_savegame,
        before={faction.id: Standing(leader_id=faction.leader_id, is_defeated=False)},
        report=GameReport(seed=1, policy="even"),
    )

    assert result == {
        faction.id: Standing(leader_id=faction.leader_id, is_defeated=False, roster_ids=frozenset({faction.leader_id}))
    }
