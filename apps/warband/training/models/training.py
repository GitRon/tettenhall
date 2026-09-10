import random
import typing

from django.db import models
from django.db.models import UniqueConstraint

from apps.warband.faction.models import Faction
from apps.warband.training.managers.training import TrainingManager


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

    # What each category can grow, and the only place that decides it. The month rolls one of these
    # attributes and the training form tells the player which - a category naming nothing is a choice
    # made blind, and two copies of the mapping would let the label and the roll drift apart.
    CATEGORY_ATTRIBUTES: typing.ClassVar[dict[int, tuple[str, ...]]] = {
        TrainingCategory.WEAPON_MASTERY: ("strength", "morale"),
        TrainingCategory.SWIFTNESS: ("dexterity",),
        TrainingCategory.SHIELD_WALL: ("health", "morale"),
    }

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

    @classmethod
    def attributes_display_for_category(cls, *, category: int) -> str:
        """
        What a category grows, written the way the overview's columns are headed.

        One phrasing rule rather than one per screen: the form's help text names all three
        categories and the overview names the chosen one, and a card reading "Strength or Morale"
        against a column headed "strength" is the mismatch this exists to prevent.
        """
        return " or ".join(attribute.capitalize() for attribute in cls.CATEGORY_ATTRIBUTES[category])

    @property
    def grown_attributes_display(self) -> str:
        """
        What this training grows. The mapping the month rolls from, read for a single row.
        """
        return self.attributes_display_for_category(category=self.category)

    def get_random_attribute_and_improvement_for_category(self, *, category: int) -> tuple[str, int]:
        """
        Determine which attribute gets improved and by how much.
        """
        attribute_options = self.CATEGORY_ATTRIBUTES.get(category)
        if attribute_options is None:
            raise RuntimeError("Invalid training category provided.")

        attribute = random.choice(attribute_options)

        # Rounded to an int: the improvement ends up in a progress bar stored as a positive small
        # integer, so a float would only survive until the next refresh from the database.
        #
        # Floored at 1 rather than 0: a roll below 0.5 rounds to nothing, which at these parameters is
        # about one month in six, and a month of training that moves no bar at all is indistinguishable
        # from a bug to the player watching it.
        improvement = max(round(random.gauss(self.TRAINING_IMPROVEMENT_MU, self.TRAINING_IMPROVEMENT_SIGMA)), 1)

        return attribute, improvement
