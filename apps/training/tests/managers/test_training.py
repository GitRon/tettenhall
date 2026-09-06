import pytest

from apps.faction.tests.factories.faction import FactionFactory
from apps.training.models import Training
from apps.training.tests.factories.training import TrainingFactory


@pytest.mark.django_db
def test_filter_faction_excludes_the_regimen_of_another_faction():
    training = TrainingFactory(faction=FactionFactory())
    TrainingFactory(faction=FactionFactory())

    result = Training.objects.filter_faction(faction_id=training.faction_id)

    assert list(result) == [training]
