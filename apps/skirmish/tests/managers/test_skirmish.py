import pytest

from apps.skirmish.models.skirmish import Skirmish
from apps.skirmish.tests.factories.skirmish import SkirmishFactory


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
