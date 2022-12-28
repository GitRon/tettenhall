from django.db import models

from apps.skirmish.models.faction import Faction
from apps.skirmish.models.item import Item


class Warrior(models.Model):
    name = models.CharField("Name", max_length=100)
    faction = models.ForeignKey(
        Faction, verbose_name="Faction", on_delete=models.CASCADE
    )

    current_health = models.PositiveSmallIntegerField("Current health")
    max_health = models.PositiveSmallIntegerField("Maximum health")

    dexterity = models.PositiveSmallIntegerField("Dexterity")

    weapon = models.ForeignKey(
        Item,
        verbose_name="Weapon",
        related_name="warrior_weapons",
        on_delete=models.CASCADE,
    )
    armor = models.ForeignKey(
        Item,
        verbose_name="Armor",
        related_name="warrior_armor",
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = "Warrior"
        verbose_name_plural = "Warriors"
        default_related_name = "warriors"

    def __str__(self):
        return self.name
