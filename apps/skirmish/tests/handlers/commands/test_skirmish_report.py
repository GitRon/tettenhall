import pytest

from apps.item.tests.factories.item import ItemFactory
from apps.skirmish.handlers.commands.skirmish_report import handle_record_skirmish_spoil, handle_record_warrior_growth
from apps.skirmish.messages.commands.skirmish_report import RecordSkirmishSpoil, RecordWarriorGrowth
from apps.skirmish.messages.events.skirmish_report import SkirmishSpoilRecorded, WarriorGrowthRecorded
from apps.skirmish.models.skirmish_spoil import SkirmishSpoil
from apps.skirmish.models.skirmish_warrior_growth import SkirmishWarriorGrowth
from apps.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_handle_record_skirmish_spoil_writes_the_row():
    skirmish = SkirmishFactory()
    item = ItemFactory(savegame=skirmish.attacking_faction.savegame)

    result = handle_record_skirmish_spoil(
        context=RecordSkirmishSpoil(
            skirmish=skirmish,
            faction=skirmish.attacking_faction,
            kind=SkirmishSpoil.KindChoices.KIND_ITEM_TAKEN,
            item=item,
        )
    )

    assert result == SkirmishSpoilRecorded(spoil=SkirmishSpoil.objects.get())
    assert SkirmishSpoil.objects.get().item == item


@pytest.mark.django_db
def test_handle_record_warrior_growth_stamps_the_side_the_man_fought_on():
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.defending_faction)

    result = handle_record_warrior_growth(
        context=RecordWarriorGrowth(skirmish=skirmish, warrior=warrior, gained_experience=10)
    )

    assert result == WarriorGrowthRecorded(growth=SkirmishWarriorGrowth.objects.get())
    assert SkirmishWarriorGrowth.objects.get().faction == skirmish.defending_faction
