from django.db import models


class Training(models.Model):
    class TrainingCategory(models.IntegerChoices):
        WEAPON_MASTERY = 1, "Weapon mastery"
        SWIFTNESS = 2, "Swiftness"
        SHIELD_WALL = 3, "Shield wall"

    category = models.PositiveSmallIntegerField("Category", choices=TrainingCategory.choices, unique=True)

    class Meta:
        verbose_name = "Training"
        verbose_name_plural = "Trainings"
        default_related_name = "trainings"

    def __str__(self):
        return f"{self.get_category_display()}"
