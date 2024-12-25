from django.db import models

from apps.faction.models.faction import Faction


class Quest(models.Model):
    # TODO: duration

    class DifficultyChoices(models.IntegerChoices):
        DIFFICULTY_EASY = 1, "Easy"
        DIFFICULTY_HARD = 2, "Hard"

    name = models.CharField("Name", max_length=50)
    # TODO: think about rename to "target_faction"
    faction = models.ForeignKey(Faction, verbose_name="Target faction", on_delete=models.CASCADE)
    difficulty = models.PositiveSmallIntegerField("Difficulty", choices=DifficultyChoices.choices)

    class Meta:
        verbose_name = "Quest"
        verbose_name_plural = "Quests"
        default_related_name = "quests"

    def __str__(self) -> str:
        return self.name
