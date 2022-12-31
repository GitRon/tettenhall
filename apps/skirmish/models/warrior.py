from django.db import models

from apps.skirmish.managers.warrior import WarriorManager
from apps.skirmish.models.faction import Faction
from apps.skirmish.models.item import Item


class Warrior(models.Model):
    class ConditionChoices(models.IntegerChoices):
        CONDITION_HEALTHY = 1, "Healthy"
        CONDITION_UNCONSCIOUS = 2, "Unconscious"
        CONDITION_DEAD = 3, "dead"

    name = models.CharField("Name", max_length=100)
    faction = models.ForeignKey(
        Faction, verbose_name="Faction", on_delete=models.CASCADE
    )

    current_health = models.SmallIntegerField("Current health")
    max_health = models.PositiveSmallIntegerField("Maximum health")
    condition = models.PositiveSmallIntegerField(
        "Condition",
        choices=ConditionChoices.choices,
        default=ConditionChoices.CONDITION_HEALTHY,
    )

    dexterity = models.PositiveSmallIntegerField("Dexterity")

    # todo one2one relationship?
    weapon = models.ForeignKey(
        Item,
        verbose_name="Weapon",
        related_name="warrior_weapons",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    # todo one2one relationship?
    armor = models.ForeignKey(
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
    def is_healthy(self):
        return self.condition == self.ConditionChoices.CONDITION_HEALTHY


class FightAction(models.Model):
    class TypeChoices(models.IntegerChoices):
        ATTACK_SIMPLE = 1, "Simple attack"

    type = models.PositiveSmallIntegerField(
        "Type", choices=TypeChoices.choices, unique=True
    )

    def __str__(self):
        return self.get_type_display()
