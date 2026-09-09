import pytest

from apps.warband.item.tests.factories.item import ItemFactory
from apps.warband.skirmish.models.skirmish_spoil import SkirmishSpoil
from apps.warband.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.warband.skirmish.tests.factories.skirmish_spoil import SkirmishSpoilFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_create_record_stores_every_part_of_the_spoil():
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.defending_faction)
    item = ItemFactory(savegame=skirmish.attacking_faction.savegame)

    spoil = SkirmishSpoil.objects.create_record(
        skirmish=skirmish,
        faction=skirmish.attacking_faction,
        kind=SkirmishSpoil.KindChoices.KIND_ITEM_TAKEN,
        item=item,
        warrior=warrior,
    )

    assert spoil.kind == SkirmishSpoil.KindChoices.KIND_ITEM_TAKEN
    assert spoil.item == item


@pytest.mark.django_db
def test_for_skirmish_keeps_another_fights_spoils_out():
    spoil = SkirmishSpoilFactory()
    SkirmishSpoilFactory()

    result = SkirmishSpoil.objects.for_skirmish(skirmish_id=spoil.skirmish_id)

    assert list(result) == [spoil]
