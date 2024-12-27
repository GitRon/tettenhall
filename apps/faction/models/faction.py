from django.db import models
from django.db.models import QuerySet

from apps.faction.managers.faction import FactionManager
from apps.faction.models.culture import Culture


class Faction(models.Model):
    name = models.CharField("Name", max_length=100)
    culture = models.ForeignKey(Culture, verbose_name="Culture", on_delete=models.CASCADE)
    fyrd_reserve = models.PositiveSmallIntegerField(
        "Fyrd reserve", default=0, help_text="Number of warriors draft-able from the fyrd"
    )
    active_quest = models.ForeignKey(
        "quest.QuestContract",
        verbose_name="Active Quest",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="There can only be one active quest at a time.",
    )

    captured_warriors = models.ManyToManyField(
        "skirmish.Warrior",
        verbose_name="Captured warriors",
        blank=True,
    )

    objects = FactionManager()

    class Meta:
        verbose_name = "Faction"
        verbose_name_plural = "Factions"
        default_related_name = "factions"

    def __str__(self) -> str:
        return self.name

    def get_all_items(self) -> QuerySet:
        from apps.item.models.item import Item

        return Item.objects.filter(owner=self)
