import pytest

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.training.models import Training
from apps.warband.training.tests.factories.training import TrainingFactory


@pytest.mark.django_db
def test_filter_faction_excludes_the_regimen_of_another_faction():
    training = TrainingFactory(faction=FactionFactory())
    TrainingFactory(faction=FactionFactory())

    result = Training.objects.filter_faction(faction_id=training.faction_id)

    assert list(result) == [training]


@pytest.mark.django_db
def test_regimen_for_faction_reads_the_row_of_that_faction():
    training = TrainingFactory(faction=FactionFactory())
    TrainingFactory(faction=FactionFactory())

    result = Training.objects.regimen_for_faction(faction_id=training.faction_id)

    assert result == training


@pytest.mark.django_db
def test_regimen_for_faction_without_a_row():
    """
    Every faction owns a regimen from NewFactionCreated on, so only a savegame predating the row
    reaches this - and the month page has to survive it rather than answer with a 500.
    """
    result = Training.objects.regimen_for_faction(faction_id=FactionFactory().id)

    assert result is None
