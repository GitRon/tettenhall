import pytest

from apps.warband.skirmish.models.skirmish import Skirmish
from apps.warband.skirmish.tests.factories.skirmish import SkirmishFactory


@pytest.mark.django_db
def test_set_victor_decides_a_fight_that_is_still_open():
    skirmish = SkirmishFactory()

    result = Skirmish.objects.set_victor(skirmish=skirmish, victorious_faction=skirmish.attacking_faction)

    assert result is True
    skirmish.refresh_from_db()
    assert skirmish.victorious_faction == skirmish.attacking_faction


@pytest.mark.django_db
def test_set_victor_refuses_a_fight_that_already_has_one():
    """
    The second pass over the same fight, which is what a savegame ending force-resolves into. It holds
    its own instance of the row, so the refusal has to come off the database rather than out of memory.
    """
    skirmish = SkirmishFactory()
    Skirmish.objects.filter(pk=skirmish.pk).update(victorious_faction=skirmish.attacking_faction)

    result = Skirmish.objects.set_victor(skirmish=skirmish, victorious_faction=skirmish.defending_faction)

    assert result is False
    skirmish.refresh_from_db()
    assert skirmish.victorious_faction == skirmish.attacking_faction


@pytest.mark.django_db
def test_batter_fortification_takes_the_blow_off_the_wall():
    skirmish = SkirmishFactory(fortification_strength=20)

    result = Skirmish.objects.batter_fortification(skirmish=skirmish, damage=7)

    assert result == 7
    skirmish.refresh_from_db()
    assert skirmish.fortification_strength == 13


@pytest.mark.django_db
def test_batter_fortification_never_takes_more_than_is_left():
    skirmish = SkirmishFactory(fortification_strength=5)

    result = Skirmish.objects.batter_fortification(skirmish=skirmish, damage=7)

    assert result == 5
    assert skirmish.fortification_strength == 0


@pytest.mark.django_db
def test_batter_fortification_leaves_the_starting_wall_standing():
    skirmish = SkirmishFactory(fortification_strength=20, starting_fortification_strength=20)

    Skirmish.objects.batter_fortification(skirmish=skirmish, damage=7)

    skirmish.refresh_from_db()
    assert skirmish.starting_fortification_strength == 20


@pytest.mark.django_db
def test_under_way_besides_finds_another_started_fight():
    skirmish = SkirmishFactory()
    other_skirmish = SkirmishFactory(current_round=2)

    assert list(Skirmish.objects.under_way_besides(skirmish=skirmish)) == [other_skirmish]


@pytest.mark.django_db
def test_under_way_besides_leaves_out_the_fight_itself():
    skirmish = SkirmishFactory(current_round=2)

    assert not Skirmish.objects.under_way_besides(skirmish=skirmish).exists()


@pytest.mark.django_db
def test_under_way_besides_leaves_out_a_fight_not_yet_started():
    skirmish = SkirmishFactory()
    SkirmishFactory(current_round=1)

    assert not Skirmish.objects.under_way_besides(skirmish=skirmish).exists()


@pytest.mark.django_db
def test_under_way_besides_leaves_out_a_decided_fight():
    skirmish = SkirmishFactory()
    decided_skirmish = SkirmishFactory(current_round=2)
    decided_skirmish.victorious_faction = decided_skirmish.attacking_faction
    decided_skirmish.save()

    assert not Skirmish.objects.under_way_besides(skirmish=skirmish).exists()
