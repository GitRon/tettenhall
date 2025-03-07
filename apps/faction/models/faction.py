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
    active_quests = models.ManyToManyField(
        "quest.QuestContract",
        verbose_name="Active Quest",
        blank=True,
        help_text="There can only be one active quest at a time.",
    )
    leader = models.ForeignKey(
        "skirmish.Warrior",
        verbose_name="Leader",
        related_name="leading_factions",
        on_delete=models.CASCADE,
        null=True,
        blank=False,
    )

    captured_warriors = models.ManyToManyField(
        "skirmish.Warrior",
        verbose_name="Captured warriors",
        blank=True,
    )
    savegame = models.ForeignKey("savegame.Savegame", verbose_name="Savegame", on_delete=models.CASCADE)

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
