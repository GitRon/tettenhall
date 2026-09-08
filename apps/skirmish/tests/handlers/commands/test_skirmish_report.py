import pytest

from apps.common.domain.dice import DiceNotation, DiceRoll
from apps.item.models.item_type import ItemType
from apps.item.tests.factories.item import ItemFactory
from apps.item.tests.factories.item_type import ItemTypeFactory
from apps.skirmish.choices.blow_outcome import BlowOutcomeChoices
from apps.skirmish.choices.skirmish_action import SkirmishActionChoices
from apps.skirmish.domain.action_roll import ActionRoll
from apps.skirmish.handlers.commands.skirmish_report import (
    handle_record_skirmish_blow,
    handle_record_skirmish_casualty,
    handle_record_skirmish_spoil,
    handle_record_warrior_growth,
)
from apps.skirmish.messages.commands.skirmish_report import (
    RecordSkirmishBlow,
    RecordSkirmishCasualty,
    RecordSkirmishSpoil,
    RecordWarriorGrowth,
)
from apps.skirmish.messages.events.skirmish_report import (
    SkirmishBlowRecorded,
    SkirmishCasualtyRecorded,
    SkirmishSpoilRecorded,
    WarriorGrowthRecorded,
)
from apps.skirmish.models.skirmish_blow import SkirmishBlow
from apps.skirmish.models.skirmish_casualty import SkirmishCasualty
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
def test_handle_record_skirmish_casualty_writes_the_fate():
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.defending_faction)

    result = handle_record_skirmish_casualty(
        context=RecordSkirmishCasualty(
            skirmish=skirmish, warrior=warrior, fate=SkirmishCasualty.FateChoices.FATE_KILLED
        )
    )

    assert result == SkirmishCasualtyRecorded(casualty=SkirmishCasualty.objects.get())
    assert SkirmishCasualty.objects.get().fate == SkirmishCasualty.FateChoices.FATE_KILLED


@pytest.mark.django_db
def test_handle_record_warrior_growth_stamps_the_side_the_man_fought_on():
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.defending_faction)

    result = handle_record_warrior_growth(
        context=RecordWarriorGrowth(skirmish=skirmish, warrior=warrior, gained_experience=10)
    )

    assert result == WarriorGrowthRecorded(growth=SkirmishWarriorGrowth.objects.get())
    assert SkirmishWarriorGrowth.objects.get().faction == skirmish.defending_faction


@pytest.mark.django_db
def test_handle_record_skirmish_blow_writes_the_row():
    skirmish = SkirmishFactory()
    attacker = WarriorFactory(faction=skirmish.attacking_faction)
    defender = WarriorFactory(faction=skirmish.defending_faction)
    weapon_type = ItemTypeFactory(base_value="2d6")
    armor_type = ItemTypeFactory(base_value="1d4", function=ItemType.FunctionChoices.FUNCTION_ARMOR)

    result = handle_record_skirmish_blow(
        context=RecordSkirmishBlow(
            skirmish=skirmish,
            round_number=4,
            attacker=attacker,
            attacker_action=SkirmishActionChoices.RISKY_ATTACK,
            attack=ActionRoll(
                roll=DiceRoll(notation=DiceNotation(dice_string="2d6", modifier=1), result=11),
                item_type=weapon_type,
                value=22,
            ),
            defender=defender,
            defender_action=SkirmishActionChoices.SIMPLE_ATTACK,
            defense=ActionRoll(
                roll=DiceRoll(notation=DiceNotation(dice_string="1d4"), result=3), item_type=armor_type, value=3
            ),
            outcome=BlowOutcomeChoices.OUTCOME_HIT,
            damage=19,
        )
    )

    assert result == SkirmishBlowRecorded(blow=SkirmishBlow.objects.get())
    assert (SkirmishBlow.objects.get().round_number, SkirmishBlow.objects.get().attack_roll) == (4, 11)
