import pytest

from apps.warband.faction.services.attack_standing import AttackRefusal, AttackStanding, get_attack_standing
from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.savegame.models.savegame import Savegame
from apps.warband.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory


@pytest.fixture
def savegame_ready_to_march(current_savegame) -> Savegame:
    """The player's faction with a healthy, unbooked leader, which every attack needs first."""
    faction = current_savegame.player_faction
    faction.leader = WarriorFactory(faction=faction)
    faction.save()

    return current_savegame


@pytest.mark.django_db
def test_get_attack_standing_offers_a_standing_rival_to_a_free_war_band(savegame_ready_to_march):
    rival_faction = FactionFactory(savegame=savegame_ready_to_march)
    WarriorFactory(faction=rival_faction)

    assert get_attack_standing(savegame=savegame_ready_to_march) == AttackStanding(
        attackable_rival_ids=frozenset({rival_faction.id}), refusals={}, war_band_refusal=None
    )


@pytest.mark.django_db
def test_get_attack_standing_blames_the_rival_whose_men_are_committed(savegame_ready_to_march):
    rival_faction = FactionFactory(savegame=savegame_ready_to_march)
    committed_defender = WarriorFactory(faction=rival_faction)
    SkirmishFactory(defending_faction=rival_faction).defending_warriors.add(committed_defender)

    standing = get_attack_standing(savegame=savegame_ready_to_march)

    assert standing.refusals == {rival_faction.id: AttackRefusal.WAR_BAND_IS_COMMITTED}
    assert standing.war_band_refusal is None


@pytest.mark.django_db
def test_get_attack_standing_says_the_war_band_has_marched(savegame_ready_to_march):
    player_faction = savegame_ready_to_march.player_faction
    rival_faction = FactionFactory(savegame=savegame_ready_to_march)
    WarriorFactory(faction=rival_faction)
    SkirmishFactory(
        attacking_faction=player_faction,
        attacking_leader=player_faction.leader,
        defending_faction=FactionFactory(savegame=savegame_ready_to_march),
        month=savegame_ready_to_march.current_month,
    ).attacking_warriors.add(player_faction.leader)

    standing = get_attack_standing(savegame=savegame_ready_to_march)

    assert standing.refusals == {rival_faction.id: AttackRefusal.HAS_MARCHED_THIS_MONTH}
    assert standing.war_band_refusal == AttackRefusal.HAS_MARCHED_THIS_MONTH


@pytest.mark.django_db
def test_get_attack_standing_says_the_war_band_has_marched_under_a_successor(savegame_ready_to_march):
    """
    A successor from home is fit and free, so the leader alone would call the war band ready to march.
    """
    player_faction = savegame_ready_to_march.player_faction
    rival_faction = FactionFactory(savegame=savegame_ready_to_march)
    WarriorFactory(faction=rival_faction)
    SkirmishFactory(
        attacking_faction=player_faction,
        attacking_leader=WarriorFactory(faction=player_faction),
        defending_faction=FactionFactory(savegame=savegame_ready_to_march),
        month=savegame_ready_to_march.current_month,
    )

    standing = get_attack_standing(savegame=savegame_ready_to_march)

    assert standing.war_band_refusal == AttackRefusal.HAS_MARCHED_THIS_MONTH


@pytest.mark.django_db
def test_get_attack_standing_says_the_leader_cannot_march(current_savegame):
    """A faction without a leader is what a captured or killed one leaves behind."""
    rival_faction = FactionFactory(savegame=current_savegame)
    WarriorFactory(faction=rival_faction)

    standing = get_attack_standing(savegame=current_savegame)

    assert standing.refusals == {rival_faction.id: AttackRefusal.LEADER_CANNOT_MARCH}
    assert standing.war_band_refusal == AttackRefusal.LEADER_CANNOT_MARCH


@pytest.mark.django_db
def test_get_attack_standing_names_the_decided_savegame_rather_than_the_rivals_men(savegame_ready_to_march):
    """
    A free leader and nobody attackable would otherwise read as "their men are spoken for", on every
    standing rival of a game nobody will play on.
    """
    rival_faction = FactionFactory(savegame=savegame_ready_to_march)
    WarriorFactory(faction=rival_faction)
    savegame_ready_to_march.outcome = Savegame.OutcomeChoices.OUTCOME_LOST
    savegame_ready_to_march.save()

    standing = get_attack_standing(savegame=savegame_ready_to_march)

    assert standing.refusals == {rival_faction.id: AttackRefusal.SAVEGAME_IS_OVER}
    assert standing.war_band_refusal == AttackRefusal.SAVEGAME_IS_OVER


@pytest.mark.django_db
def test_get_attack_standing_explains_nothing_about_a_defeated_rival(current_savegame):
    """A knocked-out faction never offered a fight, so there is no missing button to explain."""
    defeated_faction = FactionFactory(savegame=current_savegame, is_defeated=True)
    WarriorFactory(faction=defeated_faction)

    assert get_attack_standing(savegame=current_savegame) == AttackStanding(
        attackable_rival_ids=frozenset(), refusals={}, war_band_refusal=None
    )


@pytest.mark.django_db
def test_get_attack_standing_without_a_player_faction(savegame_without_player_faction):
    assert get_attack_standing(savegame=savegame_without_player_faction) == AttackStanding(
        attackable_rival_ids=frozenset(), refusals={}, war_band_refusal=None
    )
