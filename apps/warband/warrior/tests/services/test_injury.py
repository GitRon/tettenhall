from unittest import mock

import pytest

from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.warrior.models.injury_type import InjuryType
from apps.warband.warrior.services.injury import InjuryRollService
from apps.warband.warrior.tests.factories.injury_type import InjuryTypeFactory


@pytest.mark.django_db
def test_chance_at_the_lip_is_the_lower_bound():
    warrior = WarriorFactory(max_health=20)

    service = InjuryRollService(warrior=warrior, overkill_health=0)

    assert service.chance == InjuryRollService.CHANCE_AT_ZERO


@pytest.mark.django_db
def test_chance_at_the_death_threshold_is_the_upper_bound():
    # Three points is the whole band for a man who can hold twenty, DEATH_OVERKILL_SHARE being 0.15
    warrior = WarriorFactory(max_health=20)

    service = InjuryRollService(warrior=warrior, overkill_health=3)

    assert service.chance == InjuryRollService.CHANCE_AT_DEATHS_DOOR


@pytest.mark.django_db
def test_chance_scales_with_the_overkill_depth():
    warrior = WarriorFactory(max_health=20)

    service = InjuryRollService(warrior=warrior, overkill_health=1)

    assert service.chance == pytest.approx(0.2333, abs=0.0001)


@pytest.mark.django_db
def test_process_returns_nothing_when_the_roll_misses():
    warrior = WarriorFactory(max_health=20)

    with mock.patch("apps.warband.warrior.services.injury.random.random", return_value=0.99):
        result = InjuryRollService(warrior=warrior, overkill_health=3).process()

    assert result is None


@pytest.mark.django_db
def test_process_draws_an_injury_when_the_roll_lands():
    warrior = WarriorFactory(max_health=20)

    with mock.patch("apps.warband.warrior.services.injury.random.random", return_value=0.0):
        result = InjuryRollService(warrior=warrior, overkill_health=3).process()

    assert isinstance(result, InjuryType)


@pytest.mark.django_db
def test_process_raises_when_the_catalogue_is_empty():
    warrior = WarriorFactory(max_health=20)
    # The shipped fixture is loaded for the whole session, so an empty catalogue has to be made
    InjuryType.objects.all().delete()

    with (
        mock.patch("apps.warband.warrior.services.injury.random.random", return_value=0.0),
        pytest.raises(RuntimeError, match="No injury types exist"),
    ):
        InjuryRollService(warrior=warrior, overkill_health=3).process()


@pytest.mark.django_db
def test_process_draws_from_the_catalogue_it_is_given():
    warrior = WarriorFactory(max_health=20)
    InjuryType.objects.all().delete()
    injury_type = InjuryTypeFactory(name="Ruined shoulder")

    with mock.patch("apps.warband.warrior.services.injury.random.random", return_value=0.0):
        result = InjuryRollService(warrior=warrior, overkill_health=3).process()

    assert result == injury_type
