from apps.town.tests.factories.town import TownFactory


def test_str_returns_the_name_of_the_owning_faction():
    town = TownFactory.build(faction__name="Tettenhall")

    assert str(town) == "Tettenhall"
