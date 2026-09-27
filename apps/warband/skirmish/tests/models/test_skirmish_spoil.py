import pytest

from apps.warband.item.tests.factories.item import ItemFactory
from apps.warband.skirmish.models.skirmish_spoil import SkirmishSpoil
from apps.warband.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.warband.skirmish.tests.factories.skirmish_spoil import SkirmishSpoilFactory


def test_str_names_the_kind_and_the_fight():
    spoil = SkirmishSpoilFactory.build(
        kind=SkirmishSpoil.KindChoices.KIND_QUEST_REWARD,
        skirmish=SkirmishFactory.build(name="Raid on Tamworth"),
    )

    assert str(spoil) == "Quest reward (Raid on Tamworth)"


@pytest.mark.django_db
def test_a_spoil_outlives_its_item_and_still_names_it():
    item = ItemFactory()
    spoil = SkirmishSpoilFactory(kind=SkirmishSpoil.KindChoices.KIND_ITEM_TAKEN, item=item)
    item_name = spoil.item_name

    item.delete()

    spoil.refresh_from_db()
    assert (spoil.item, spoil.item_name) == (None, item_name)
