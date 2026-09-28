import pytest

from apps.warband.skirmish.models.skirmish_casualty import SkirmishCasualty
from apps.warband.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.warband.skirmish.tests.factories.skirmish_casualty import SkirmishCasualtyFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_create_record_creates_the_row_on_the_first_fate():
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.attacking_faction)

    casualty = SkirmishCasualty.objects.create_record(
        skirmish=skirmish, warrior=warrior, fate=SkirmishCasualty.FateChoices.FATE_KILLED
    )

    assert casualty.fate == SkirmishCasualty.FateChoices.FATE_KILLED
    assert SkirmishCasualty.objects.count() == 1


@pytest.mark.django_db
def test_create_record_overwrites_the_fate_of_a_man_already_recorded():
    """
    The case of every prisoner in the game: knocked out first, taken once the fight was decided.
    """
    existing = SkirmishCasualtyFactory(fate=SkirmishCasualty.FateChoices.FATE_INCAPACITATED)

    casualty = SkirmishCasualty.objects.create_record(
        skirmish=existing.skirmish, warrior=existing.warrior, fate=SkirmishCasualty.FateChoices.FATE_CAPTURED
    )

    assert casualty.fate == SkirmishCasualty.FateChoices.FATE_CAPTURED
    assert SkirmishCasualty.objects.count() == 1


@pytest.mark.django_db
def test_for_skirmish_keeps_another_fights_casualty_out():
    casualty = SkirmishCasualtyFactory()
    SkirmishCasualtyFactory()

    result = SkirmishCasualty.objects.for_skirmish(skirmish_id=casualty.skirmish_id)

    assert list(result) == [casualty]
