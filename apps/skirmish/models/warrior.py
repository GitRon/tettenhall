from django.db import models

from apps.core.domain.random import DiceNotation
from apps.faction.models.culture import Culture
from apps.faction.models.faction import Faction
from apps.item.models.item import Item
from apps.item.models.item_type import ItemType
from apps.skirmish.managers.warrior import WarriorManager


class Warrior(models.Model):
    NO_WEAPON_ATTACK = "1d3"
    NO_ARMOR_DEFENSE = "1d3"

    class ConditionChoices(models.IntegerChoices):
        CONDITION_HEALTHY = 1, "Healthy"
        CONDITION_UNCONSCIOUS = 2, "Unconscious"
        CONDITION_FLEEING = 3, "Fleeing"
        CONDITION_DEAD = 4, "Dead"

    name = models.CharField("Name", max_length=100)
    culture = models.ForeignKey(Culture, verbose_name="Culture", on_delete=models.CASCADE)
    faction = models.ForeignKey(Faction, verbose_name="Faction", null=True, blank=True, on_delete=models.CASCADE)

    strength = models.PositiveSmallIntegerField("Strength")
    strength_progress = models.PositiveSmallIntegerField("Strength progress", default=0)

    dexterity = models.PositiveSmallIntegerField("Dexterity")
    dexterity_progress = models.PositiveSmallIntegerField("Dexterity progress", default=0)

    current_health = models.SmallIntegerField("Current health")
    max_health = models.PositiveSmallIntegerField("Maximum health")
    health_progress = models.PositiveSmallIntegerField("Health progress", default=0)

    current_morale = models.SmallIntegerField("Current morale")
    max_morale = models.PositiveSmallIntegerField("Maximum morale")
    morale_progress = models.PositiveSmallIntegerField("Morale progress", default=0)

    experience = models.PositiveIntegerField("Experience", default=0)
    weekly_salary = models.PositiveSmallIntegerField("Weekly salary", default=0)

    recruitment_price = models.PositiveSmallIntegerField("Recruitment price", default=0)

    condition = models.PositiveSmallIntegerField(
        "Condition",
        choices=ConditionChoices.choices,
        default=ConditionChoices.CONDITION_HEALTHY,
    )

    weapon = models.OneToOneField(
        Item,
        verbose_name="Weapon",
        related_name="warrior_weapon",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    armor = models.OneToOneField(
        Item,
        verbose_name="Armor",
        related_name="warrior_armor",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )

    objects = WarriorManager()

    class Meta:
        verbose_name = "Warrior"
        verbose_name_plural = "Warriors"
        default_related_name = "warriors"

    def __str__(self):
        return self.name

    @property
    def is_dead(self):
        return self.condition == self.ConditionChoices.CONDITION_DEAD

    @property
    def is_unconscious(self):
        return self.condition == self.ConditionChoices.CONDITION_UNCONSCIOUS

    @property
    def is_fleeing(self):
        return self.condition == self.ConditionChoices.CONDITION_FLEEING

    @property
    def is_healthy(self):
        return self.condition == self.ConditionChoices.CONDITION_HEALTHY

    def get_weapon_or_fallback(self) -> Item:
        return (
            self.weapon
            if self.weapon
            else Item(
                type=ItemType.objects.get(is_fallback=True, function=ItemType.FunctionChoices.FUNCTION_WEAPON),
                owner=self.faction,
            )
        )

    def get_armor_or_fallback(self) -> Item:
        return (
            self.armor
            if self.armor
            else Item(
                type=ItemType.objects.get(is_fallback=True, function=ItemType.FunctionChoices.FUNCTION_ARMOR),
                owner=self.faction,
            )
        )

    def roll_attack(self):
        item = self.get_weapon_or_fallback()
        return DiceNotation(dice_string=item.type.base_value, modifier=item.modifier).result

    def roll_defense(self):
        item = self.get_armor_or_fallback()
        return DiceNotation(dice_string=item.type.base_value, modifier=item.modifier).result


class SkirmishAction(models.Model):
    class TypeChoices(models.IntegerChoices):
        SIMPLE_ATTACK = 1, "Simple attack"
        RISKY_ATTACK = 2, "Risky attack"

    type = models.PositiveSmallIntegerField("Type", choices=TypeChoices.choices, unique=True)

    def __str__(self):
        return self.get_type_display()
