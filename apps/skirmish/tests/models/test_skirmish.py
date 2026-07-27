from apps.skirmish.tests.factories.skirmish import SkirmishFactory


def test_str_returns_the_name():
    skirmish = SkirmishFactory.build(name="Raid on Tettenhall")

    assert str(skirmish) == "Raid on Tettenhall"
