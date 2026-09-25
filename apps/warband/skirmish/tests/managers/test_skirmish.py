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
