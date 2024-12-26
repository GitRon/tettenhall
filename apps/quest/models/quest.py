from django.db import models

from apps.faction.models.faction import Faction


class Quest(models.Model):
    class DifficultyChoices(models.IntegerChoices):
        DIFFICULTY_EASY = 1, "Easy"
        DIFFICULTY_HARD = 2, "Hard"

    name = models.CharField("Name", max_length=50)
    loot = models.PositiveSmallIntegerField("Loot (in silver)")
    target_faction = models.ForeignKey(Faction, verbose_name="Target faction", on_delete=models.CASCADE)
    difficulty = models.PositiveSmallIntegerField("Difficulty", choices=DifficultyChoices.choices)

    class Meta:
        verbose_name = "Quest"
        verbose_name_plural = "Quests"
        default_related_name = "quests"

    def __str__(self) -> str:
        return self.name

    def get_min_max_number_of_opponents(self) -> (int, int):
        """
        Calculates the minimum and maximum number of opponents a player will encounter when resolving (fighting)
        a quest contract.
        """
        if self.difficulty == self.DifficultyChoices.DIFFICULTY_EASY:
            return 3, 5
        if self.difficulty == self.DifficultyChoices.DIFFICULTY_HARD:
            return 4, 8
        raise RuntimeError("Invalid difficulty choice.")
