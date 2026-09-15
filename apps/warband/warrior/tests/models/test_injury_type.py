import pytest

from apps.warband.warrior.models.injury_type import InjuryType
from apps.warband.warrior.tests.factories.injury_type import InjuryTypeFactory


@pytest.mark.django_db
def test_str_is_the_name():
    injury_type = InjuryTypeFactory(name="Stiff ankle")

    assert str(injury_type) == "Stiff ankle"


@pytest.mark.django_db
def test_description_names_the_thing_and_its_price():
    injury_type = InjuryTypeFactory(
        name="Crushed hand",
        attribute=InjuryType.AttributeChoices.ATTRIBUTE_DEXTERITY,
        magnitude=2,
    )

    assert injury_type.description == "Crushed hand (-2 Dexterity)"
