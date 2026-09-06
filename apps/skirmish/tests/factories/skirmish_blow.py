import factory
from factory.django import DjangoModelFactory

from apps.item.models.item_type import ItemType
from apps.item.tests.factories.item_type import ItemTypeFactory
from apps.skirmish.choices.blow_outcome import BlowOutcomeChoices
from apps.skirmish.choices.skirmish_action import SkirmishActionChoices
from apps.skirmish.models.skirmish_blow import SkirmishBlow
from apps.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.skirmish.tests.factories.warrior import WarriorFactory


class SkirmishBlowFactory(DjangoModelFactory):
    class Meta:
        model = SkirmishBlow

    skirmish = factory.SubFactory(SkirmishFactory)
    round_number = 1
    attacker = factory.SubFactory(WarriorFactory, faction=factory.SelfAttribute("..skirmish.attacking_faction"))
    attacker_action = SkirmishActionChoices.SIMPLE_ATTACK
    defender = factory.SubFactory(WarriorFactory, faction=factory.SelfAttribute("..skirmish.defending_faction"))
    defender_action = SkirmishActionChoices.SIMPLE_ATTACK

    outcome = BlowOutcomeChoices.OUTCOME_HIT

    attack_item_type = factory.SubFactory(ItemTypeFactory, base_value="2d6")
    attack_dice = "2d6"
    attack_modifier = 1
    attack_roll = 8
    attack_value = 8

    defense_item_type = factory.SubFactory(
        ItemTypeFactory, base_value="1d4", function=ItemType.FunctionChoices.FUNCTION_ARMOR
    )
    defense_dice = "1d4"
    defense_modifier = 0
    defense_roll = 3
    defense_value = 3

    damage = 5
