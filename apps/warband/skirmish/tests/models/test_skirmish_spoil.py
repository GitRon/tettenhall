from apps.warband.skirmish.models.skirmish_spoil import SkirmishSpoil
from apps.warband.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.warband.skirmish.tests.factories.skirmish_spoil import SkirmishSpoilFactory


def test_str_names_the_kind_and_the_fight():
    spoil = SkirmishSpoilFactory.build(
        kind=SkirmishSpoil.KindChoices.KIND_QUEST_REWARD,
        skirmish=SkirmishFactory.build(name="Raid on Tamworth"),
    )

    assert str(spoil) == "Quest reward (Raid on Tamworth)"
