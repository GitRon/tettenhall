import random

from django.db import models
from django.db.models import UniqueConstraint

from apps.faction.models import Faction
from apps.training.managers.training import TrainingManager


class Training(models.Model):
    """
    This model stores what will be trained in the current month.
    """

    TRAINING_IMPROVEMENT_MU = 15
    TRAINING_IMPROVEMENT_SIGMA = 15

    class TrainingCategory(models.IntegerChoices):
        WEAPON_MASTERY = 1, "Weapon mastery"
        SWIFTNESS = 2, "Swiftness"
        SHIELD_WALL = 3, "Shield wall"

    category = models.PositiveSmallIntegerField("Category", choices=TrainingCategory.choices)
    faction = models.ForeignKey(Faction, verbose_name="Faction", on_delete=models.CASCADE)

    objects = TrainingManager()

    class Meta:
        verbose_name = "Training"
        verbose_name_plural = "Trainings"
        default_related_name = "trainings"
        constraints = (UniqueConstraint(fields=("faction", "category"), name="unique_faction_category"),)

    def __str__(self) -> str:
        return f"{self.get_category_display()}"

    def get_random_attribute_and_improvement_for_category(self, *, category: int) -> [str, int]:
        """
        Determine which attribute gets improved and by how much.
        """
        if category == self.TrainingCategory.WEAPON_MASTERY:
            attribute = random.choice(("strength", "morale"))
        elif category == self.TrainingCategory.SWIFTNESS:
            attribute = random.choice(("dexterity",))
        elif category == self.TrainingCategory.SHIELD_WALL:
            attribute = random.choice(("health", "morale"))
        else:
            raise RuntimeError("Invalid training category provided.")

        improvement = max(random.gauss(self.TRAINING_IMPROVEMENT_MU, self.TRAINING_IMPROVEMENT_SIGMA), 0)

        return attribute, improvement
