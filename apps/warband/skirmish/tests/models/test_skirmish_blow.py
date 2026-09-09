import pytest

from apps.warband.skirmish.tests.factories.skirmish_blow import SkirmishBlowFactory


@pytest.mark.django_db
def test_str_names_both_men_and_the_round():
    blow = SkirmishBlowFactory(round_number=3)

    assert str(blow) == f"{blow.attacker} vs {blow.defender}, round 3 ({blow.skirmish})"


@pytest.mark.django_db
def test_attack_notation_rebuilds_the_die_that_was_thrown():
    blow = SkirmishBlowFactory(attack_dice="2d6", attack_modifier=1)

    result = blow.attack_notation

    assert (result.rolls, result.sides, result.modifier) == (2, 6, 1)


@pytest.mark.django_db
def test_attack_notation_for_a_blow_that_threw_no_die():
    blow = SkirmishBlowFactory(attack_dice="", attack_modifier=None, attack_roll=None)

    assert blow.attack_notation is None


@pytest.mark.django_db
def test_defense_notation_rebuilds_the_armours_die():
    blow = SkirmishBlowFactory(defense_dice="1d4", defense_modifier=2)

    result = blow.defense_notation

    assert (result.rolls, result.sides, result.modifier) == (1, 4, 2)


@pytest.mark.django_db
def test_attack_ceiling_is_what_the_weapon_could_have_rolled():
    """
    The modifier counts, because the recorded roll carries it too - measuring an 8 from "2d6+1"
    against a bare 12 would call a maximum throw an ordinary one.
    """
    blow = SkirmishBlowFactory(attack_dice="2d6", attack_modifier=1)

    assert blow.attack_ceiling == 13


@pytest.mark.django_db
def test_attack_ceiling_for_a_blow_that_threw_no_die():
    blow = SkirmishBlowFactory(attack_dice="", attack_modifier=None, attack_roll=None)

    assert blow.attack_ceiling is None


@pytest.mark.django_db
def test_defense_ceiling_is_what_the_armour_could_have_rolled():
    blow = SkirmishBlowFactory(defense_dice="1d4", defense_modifier=2)

    assert blow.defense_ceiling == 6
