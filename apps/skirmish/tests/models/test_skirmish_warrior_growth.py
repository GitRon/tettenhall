from apps.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.skirmish.tests.factories.skirmish_warrior_growth import SkirmishWarriorGrowthFactory
from apps.skirmish.tests.factories.warrior import WarriorFactory


def test_str_names_the_warrior_and_the_fight():
    growth = SkirmishWarriorGrowthFactory.build(
        warrior=WarriorFactory.build(name="Wighelm"),
        skirmish=SkirmishFactory.build(name="Raid on Tamworth"),
    )

    assert str(growth) == "Wighelm (Raid on Tamworth)"
