import pytest

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.savegame.tests.factories.savegame import SavegameFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.warrior.models.injury import Injury
from apps.warband.warrior.tests.factories.injury import InjuryFactory
from apps.warband.warrior.tests.factories.injury_type import InjuryTypeFactory


@pytest.mark.django_db
def test_str_names_the_man_and_the_mark():
    injury = InjuryFactory(warrior__name="Cuthred", type__name="Missing finger")

    assert str(injury) == "Cuthred: Missing finger"


@pytest.mark.django_db
def test_create_record_writes_the_row():
    warrior = WarriorFactory()
    injury_type = InjuryTypeFactory()

    injury = Injury.objects.create_record(warrior=warrior, injury_type=injury_type, month=7)

    assert injury.inflicted_in_month == 7
    assert list(warrior.injuries.all()) == [injury]


@pytest.mark.django_db
def test_for_warrior_narrows_to_one_man():
    injury = InjuryFactory()
    InjuryFactory()

    result = Injury.objects.for_warrior(warrior_id=injury.warrior_id)

    assert list(result) == [injury]


def test_inflicted_on_dates_the_injury_in_the_years_of_his_savegame():
    """
    The tenth month is the first Æfterra Geola, which is where the year turns - so a mark taken then
    falls in the year after the savegame opened, not in it.
    """
    savegame = SavegameFactory.build(start_year=768)
    warrior = WarriorFactory.build(faction=FactionFactory.build(savegame=savegame))
    injury = InjuryFactory.build(warrior=warrior, inflicted_in_month=10)

    result = injury.inflicted_on.label

    assert result == "Æfterra Geola · Winter · AD 769"
