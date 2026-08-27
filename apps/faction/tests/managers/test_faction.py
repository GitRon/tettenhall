import pytest

from apps.faction.models.faction import Faction
from apps.faction.tests.factories.faction import FactionFactory
from apps.savegame.tests.factories.savegame import SavegameFactory
from apps.skirmish.models.warrior import Warrior
from apps.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.skirmish.tests.factories.warrior import WarriorFactory


@pytest.fixture
def player_faction() -> Faction:
    """
    A faction ready to march: a healthy leader, free of any quest.

    Shared because every case below needs one before anything about the target is even looked at,
    and building it inline four times over would bury the rule each test is actually about.
    """
    faction = FactionFactory()
    faction.leader = WarriorFactory(faction=faction)
    faction.save()

    return faction


@pytest.mark.django_db
def test_add_captive_arrests_the_warrior():
    faction = FactionFactory()
    warrior = WarriorFactory(savegame=faction.savegame)

    Faction.objects.add_captive(faction=faction, warrior=warrior)

    assert list(faction.captured_warriors.all()) == [warrior]


@pytest.mark.django_db
def test_still_in_play_returns_the_factions_of_the_savegame():
    savegame = SavegameFactory()
    faction = FactionFactory(savegame=savegame)
    FactionFactory()

    result = Faction.objects.still_in_play(savegame_id=savegame.id)

    assert list(result) == [faction]


@pytest.mark.django_db
def test_rivals_in_play_returns_the_rival(player_faction):
    rival_faction = FactionFactory(savegame=player_faction.savegame)

    result = Faction.objects.rivals_in_play(player_faction=player_faction)

    assert list(result) == [rival_faction]


@pytest.mark.django_db
def test_rivals_in_play_excludes_the_player_faction(player_faction):
    result = Faction.objects.rivals_in_play(player_faction=player_faction)

    assert list(result) == []


@pytest.mark.django_db
def test_rivals_in_play_excludes_a_defeated_faction(player_faction):
    """
    A knocked-out rival drops off the board for the same reason it stops getting a month.
    """
    FactionFactory(savegame=player_faction.savegame, is_defeated=True)

    result = Faction.objects.rivals_in_play(player_faction=player_faction)

    assert list(result) == []


@pytest.mark.django_db
def test_rivals_in_play_excludes_factions_of_another_savegame(player_faction):
    FactionFactory()

    result = Faction.objects.rivals_in_play(player_faction=player_faction)

    assert list(result) == []


@pytest.mark.django_db
def test_attackable_by_returns_the_rival(player_faction):
    rival_faction = FactionFactory(savegame=player_faction.savegame)
    WarriorFactory(faction=rival_faction)

    result = Faction.objects.attackable_by(player_faction=player_faction, month=3)

    assert list(result) == [rival_faction]


@pytest.mark.django_db
def test_attackable_by_without_a_player_faction():
    """
    The reachable state before the player has a faction of his own: nobody to attack with.
    """
    result = Faction.objects.attackable_by(player_faction=None, month=3)

    assert list(result) == []


@pytest.mark.django_db
def test_attackable_by_without_an_available_leader(player_faction):
    """
    "The leader always joins", so an attack he cannot march on is not on offer at all.
    """
    player_faction.leader.condition = Warrior.ConditionChoices.CONDITION_UNCONSCIOUS
    player_faction.leader.save()
    rival_faction = FactionFactory(savegame=player_faction.savegame)
    WarriorFactory(faction=rival_faction)

    result = Faction.objects.attackable_by(player_faction=player_faction, month=3)

    assert list(result) == []


@pytest.mark.django_db
def test_attackable_by_excludes_the_player_faction(player_faction):
    result = Faction.objects.attackable_by(player_faction=player_faction, month=3)

    assert list(result) == []


@pytest.mark.django_db
def test_attackable_by_excludes_a_defeated_faction(player_faction):
    rival_faction = FactionFactory(savegame=player_faction.savegame, is_defeated=True)
    WarriorFactory(faction=rival_faction)

    result = Faction.objects.attackable_by(player_faction=player_faction, month=3)

    assert list(result) == []


@pytest.mark.django_db
def test_attackable_by_excludes_a_faction_without_a_healthy_warrior(player_faction):
    """
    Nobody left to defend the place. Without this the skirmish would be created with an empty side.
    """
    rival_faction = FactionFactory(savegame=player_faction.savegame)
    WarriorFactory(faction=rival_faction, condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS)

    result = Faction.objects.attackable_by(player_faction=player_faction, month=3)

    assert list(result) == []


@pytest.mark.django_db
def test_attackable_by_excludes_a_faction_whose_defenders_are_already_in_a_fight(player_faction):
    """
    Its men are healthy but committed, so the muster would field nobody and the skirmish would be
    created with an empty side. Reachable since a quest fields the target's own war band: accept one
    against a rival and its defenders are spoken for.
    """
    rival_faction = FactionFactory(savegame=player_faction.savegame)
    committed_defender = WarriorFactory(faction=rival_faction)
    SkirmishFactory(defending_faction=rival_faction).defending_warriors.add(committed_defender)

    result = Faction.objects.attackable_by(player_faction=player_faction, month=3)

    assert list(result) == []


@pytest.mark.django_db
def test_attackable_by_offers_nobody_once_the_war_band_has_marched(player_faction):
    """
    Every warrior fights once a month and the leader joins every attack, so one fight uses the month
    up - against this rival and against every other one.
    """
    rival_faction = FactionFactory(savegame=player_faction.savegame)
    WarriorFactory(faction=rival_faction)
    untouched_faction = FactionFactory(savegame=player_faction.savegame)
    WarriorFactory(faction=untouched_faction)
    skirmish = SkirmishFactory(
        attacking_faction=player_faction,
        defending_faction=rival_faction,
        victorious_faction=player_faction,
        month=3,
    )
    skirmish.attacking_warriors.add(player_faction.leader)

    result = Faction.objects.attackable_by(player_faction=player_faction, month=3)

    assert list(result) == []


@pytest.mark.django_db
def test_attackable_by_offers_a_rival_again_the_month_after(player_faction):
    rival_faction = FactionFactory(savegame=player_faction.savegame)
    WarriorFactory(faction=rival_faction)
    skirmish = SkirmishFactory(
        attacking_faction=player_faction,
        defending_faction=rival_faction,
        victorious_faction=player_faction,
        month=2,
    )
    skirmish.attacking_warriors.add(player_faction.leader)

    result = Faction.objects.attackable_by(player_faction=player_faction, month=3)

    assert list(result) == [rival_faction]


@pytest.mark.django_db
def test_attackable_by_offers_nobody_while_a_fight_is_still_undecided(player_faction):
    """
    An unresolved fight carries over: the leader is still standing on that roster, so he is not
    free to march again just because the month rolled over.
    """
    rival_faction = FactionFactory(savegame=player_faction.savegame)
    WarriorFactory(faction=rival_faction)
    skirmish = SkirmishFactory(attacking_faction=player_faction, defending_faction=rival_faction, month=2)
    skirmish.attacking_warriors.add(player_faction.leader)

    result = Faction.objects.attackable_by(player_faction=player_faction, month=3)

    assert list(result) == []


@pytest.mark.django_db
def test_attackable_by_excludes_factions_of_another_savegame(player_faction):
    foreign_faction = FactionFactory()
    WarriorFactory(faction=foreign_faction)

    result = Faction.objects.attackable_by(player_faction=player_faction, month=3)

    assert list(result) == []


@pytest.mark.django_db
def test_remove_captive_releases_the_warrior():
    faction = FactionFactory()
    warrior = WarriorFactory(savegame=faction.savegame)
    faction.captured_warriors.add(warrior)

    Faction.objects.remove_captive(faction=faction, warrior=warrior)

    assert list(faction.captured_warriors.all()) == []
