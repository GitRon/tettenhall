from django.db import models


class SkirmishAction(models.Model):
    class TypeChoices(models.IntegerChoices):
        SIMPLE_ATTACK = 1, "Simple attack"
        RISKY_ATTACK = 2, "Risky attack"

    type = models.PositiveSmallIntegerField("Type", choices=TypeChoices.choices, unique=True)

    def __str__(self) -> str:
        return self.get_type_display()
