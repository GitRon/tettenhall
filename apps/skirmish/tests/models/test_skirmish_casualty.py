from apps.skirmish.models.skirmish_casualty import SkirmishCasualty
from apps.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.skirmish.tests.factories.skirmish_casualty import SkirmishCasualtyFactory
from apps.skirmish.tests.factories.warrior import WarriorFactory


def test_str_names_the_man_his_fate_and_the_fight():
    casualty = SkirmishCasualtyFactory.build(
        warrior=WarriorFactory.build(name="Wighelm"),
        skirmish=SkirmishFactory.build(name="Raid on Tamworth"),
        fate=SkirmishCasualty.FateChoices.FATE_CAPTURED,
    )

    assert str(casualty) == "Wighelm: Taken prisoner (Raid on Tamworth)"
