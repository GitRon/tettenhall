from django.db import models

from apps.core.domain.random import DiceNotation
from apps.faction.models.faction import Faction
from apps.skirmish.managers.warrior import WarriorManager
from apps.skirmish.models.item import Item


class Warrior(models.Model):
    NO_WEAPON_ATTACK = "1d3"
    NO_ARMOR_DEFENSE = "1d3"

    class ConditionChoices(models.IntegerChoices):
        CONDITION_HEALTHY = 1, "Healthy"
        CONDITION_UNCONSCIOUS = 2, "Unconscious"
        CONDITION_FLEEING = 3, "Fleeing"
        CONDITION_DEAD = 4, "Dead"

    name = models.CharField("Name", max_length=100)
    faction = models.ForeignKey(Faction, verbose_name="Faction", on_delete=models.CASCADE)

    current_health = models.SmallIntegerField("Current health")
    max_health = models.PositiveSmallIntegerField("Maximum health")

    current_morale = models.SmallIntegerField("Current morale")
    max_morale = models.PositiveSmallIntegerField("Maximum morale")

    experience = models.PositiveIntegerField("Experience", default=0)

    condition = models.PositiveSmallIntegerField(
        "Condition",
        choices=ConditionChoices.choices,
        default=ConditionChoices.CONDITION_HEALTHY,
    )

    dexterity = models.PositiveSmallIntegerField("Dexterity")

    weapon = models.OneToOneField(
        Item,
        verbose_name="Weapon",
        related_name="warrior_weapons",
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

    def get_weapon_or_fallback(self):
        return (
            self.weapon
            if self.weapon
            else Item(type=Item.TypeChoices.TYPE_WEAPON, value=self.NO_WEAPON_ATTACK, owner=self.faction)
        )

    def get_armor_or_fallback(self):
        return (
            self.armor
            if self.armor
            else Item(type=Item.TypeChoices.TYPE_ARMOR, value=self.NO_ARMOR_DEFENSE, owner=self.faction)
        )

    def roll_attack(self):
        return DiceNotation(dice_string=self.get_weapon_or_fallback().value).result

    def roll_defense(self):
        return DiceNotation(dice_string=self.get_armor_or_fallback().value).result


class FightAction(models.Model):
    class TypeChoices(models.IntegerChoices):
        SIMPLE_ATTACK = 1, "Simple attack"
        RISKY_ATTACK = 2, "Risky attack"

    type = models.PositiveSmallIntegerField("Type", choices=TypeChoices.choices, unique=True)

    def __str__(self):
        return self.get_type_display()
