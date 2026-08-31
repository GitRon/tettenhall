import pytest

from apps.skirmish.choices.skirmish_action import SkirmishActionChoices
from apps.skirmish.models.warrior import Warrior
from apps.skirmish.services.skirmish.skirmish_participants import (
    SkirmishParticipantBuilderService,
    UnknownSkirmishParticipantError,
)
from apps.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.skirmish.tests.factories.warrior import WarriorFactory


def _fast_attacker(faction) -> Warrior:
    """
    A warrior the decision service answers "Fast attack" for: healthy, and dexterous above the mean.
    """
    return WarriorFactory(faction=faction, current_health=20, max_health=20, dexterity=20, strength=1)


@pytest.mark.django_db
def test_process_ignores_the_action_posted_for_an_enemy():
    """
    The whole defect: the enemy's card posted the AI's choice back in a field the player could edit,
    so a defensive stance chosen in devtools removed all incoming damage.
    """
    skirmish = SkirmishFactory()
    player_warrior = WarriorFactory(faction=skirmish.attacking_faction)
    enemy = _fast_attacker(skirmish.defending_faction)
    skirmish.attacking_warriors.add(player_warrior)
    skirmish.defending_warriors.add(enemy)

    _attacking, defending = SkirmishParticipantBuilderService(
        skirmish=skirmish,
        participants=[
            (player_warrior.id, SkirmishActionChoices.SIMPLE_ATTACK),
            (enemy.id, SkirmishActionChoices.DEFENSIVE_STANCE),
        ],
        player_faction_id=skirmish.attacking_faction_id,
    ).process()

    assert [participant.skirmish_action for participant in defending] == [SkirmishActionChoices.FAST_ATTACK]


@pytest.mark.django_db
def test_process_decides_the_same_action_the_enemy_posted():
    """
    Nothing changes when the posted value happened to be the honest one.
    """
    skirmish = SkirmishFactory()
    player_warrior = WarriorFactory(faction=skirmish.attacking_faction)
    enemy = _fast_attacker(skirmish.defending_faction)
    skirmish.attacking_warriors.add(player_warrior)
    skirmish.defending_warriors.add(enemy)

    _attacking, defending = SkirmishParticipantBuilderService(
        skirmish=skirmish,
        participants=[
            (player_warrior.id, SkirmishActionChoices.SIMPLE_ATTACK),
            (enemy.id, SkirmishActionChoices.FAST_ATTACK),
        ],
        player_faction_id=skirmish.attacking_faction_id,
    ).process()

    assert [participant.skirmish_action for participant in defending] == [SkirmishActionChoices.FAST_ATTACK]


@pytest.mark.django_db
def test_process_honours_the_action_posted_for_the_players_own_warrior():
    skirmish = SkirmishFactory()
    player_warrior = _fast_attacker(skirmish.attacking_faction)
    skirmish.attacking_warriors.add(player_warrior)
    skirmish.defending_warriors.add(WarriorFactory(faction=skirmish.defending_faction))

    attacking, _defending = SkirmishParticipantBuilderService(
        skirmish=skirmish,
        participants=[(player_warrior.id, SkirmishActionChoices.DEFENSIVE_STANCE)],
        player_faction_id=skirmish.attacking_faction_id,
    ).process()

    assert [participant.skirmish_action for participant in attacking] == [SkirmishActionChoices.DEFENSIVE_STANCE]


@pytest.mark.django_db
def test_process_when_the_player_is_the_defending_side():
    """
    The side split is what this story changes, and #21 exists because that distinction was got wrong
    before - being the attacker does not mean being the player.
    """
    skirmish = SkirmishFactory()
    enemy = _fast_attacker(skirmish.attacking_faction)
    player_warrior = WarriorFactory(faction=skirmish.defending_faction)
    skirmish.attacking_warriors.add(enemy)
    skirmish.defending_warriors.add(player_warrior)

    attacking, defending = SkirmishParticipantBuilderService(
        skirmish=skirmish,
        participants=[
            (enemy.id, SkirmishActionChoices.DEFENSIVE_STANCE),
            (player_warrior.id, SkirmishActionChoices.RISKY_ATTACK),
        ],
        player_faction_id=skirmish.defending_faction_id,
    ).process()

    assert [participant.skirmish_action for participant in attacking] == [SkirmishActionChoices.FAST_ATTACK]
    assert [participant.skirmish_action for participant in defending] == [SkirmishActionChoices.RISKY_ATTACK]


@pytest.mark.django_db
def test_process_without_a_player_faction_leaves_both_sides_to_the_ai():
    """
    The same answer SkirmishFightView gives: with no player faction neither side is his, so neither
    is taken from the request rather than one being guessed at.
    """
    skirmish = SkirmishFactory()
    attacker = _fast_attacker(skirmish.attacking_faction)
    defender = _fast_attacker(skirmish.defending_faction)
    skirmish.attacking_warriors.add(attacker)
    skirmish.defending_warriors.add(defender)

    attacking, defending = SkirmishParticipantBuilderService(
        skirmish=skirmish,
        participants=[
            (attacker.id, SkirmishActionChoices.DEFENSIVE_STANCE),
            (defender.id, SkirmishActionChoices.DEFENSIVE_STANCE),
        ],
        player_faction_id=None,
    ).process()

    assert [participant.skirmish_action for participant in attacking] == [SkirmishActionChoices.FAST_ATTACK]
    assert [participant.skirmish_action for participant in defending] == [SkirmishActionChoices.FAST_ATTACK]


@pytest.mark.django_db
def test_process_fields_an_enemy_the_player_did_not_post():
    """
    Overriding only the action would have left a player able to shrink the opposition by leaving one
    of them out of the request, so the roster names who fights rather than the post.
    """
    skirmish = SkirmishFactory()
    player_warrior = WarriorFactory(faction=skirmish.attacking_faction)
    skirmish.attacking_warriors.add(player_warrior)
    skirmish.defending_warriors.add(*WarriorFactory.create_batch(2, faction=skirmish.defending_faction))

    _attacking, defending = SkirmishParticipantBuilderService(
        skirmish=skirmish,
        participants=[(player_warrior.id, SkirmishActionChoices.SIMPLE_ATTACK)],
        player_faction_id=skirmish.attacking_faction_id,
    ).process()

    assert len(defending) == 2


@pytest.mark.django_db
def test_process_leaves_out_a_warrior_who_is_not_healthy():
    """
    Only the healthy fight, and only their cards ever carried a control.
    """
    skirmish = SkirmishFactory()
    skirmish.attacking_warriors.add(WarriorFactory(faction=skirmish.attacking_faction))
    fighting_enemy = WarriorFactory(faction=skirmish.defending_faction)
    skirmish.defending_warriors.add(
        fighting_enemy,
        WarriorFactory(faction=skirmish.defending_faction, condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS),
    )

    _attacking, defending = SkirmishParticipantBuilderService(
        skirmish=skirmish, participants=[], player_faction_id=skirmish.attacking_faction_id
    ).process()

    assert [participant.warrior for participant in defending] == [fighting_enemy]


@pytest.mark.django_db
def test_process_refuses_a_warrior_fighting_neither_side():
    skirmish = SkirmishFactory()
    skirmish.attacking_warriors.add(WarriorFactory(faction=skirmish.attacking_faction))
    outsider = WarriorFactory()

    service = SkirmishParticipantBuilderService(
        skirmish=skirmish,
        participants=[(outsider.id, SkirmishActionChoices.SIMPLE_ATTACK)],
        player_faction_id=skirmish.attacking_faction_id,
    )

    with pytest.raises(UnknownSkirmishParticipantError):
        service.process()
