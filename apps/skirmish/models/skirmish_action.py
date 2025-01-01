from django.db import models


# TODO: do we need this model?
class SkirmishAction(models.Model):
    class TypeChoices(models.IntegerChoices):
        SIMPLE_ATTACK = 1, "Simple attack"
        RISKY_ATTACK = 2, "Risky attack"
        FAST_ATTACK = 3, "Fast attack"
        # TODO: fast attack to counter low dex
        # TODO: defensive stance to counter low def?
        # TODO: mighty blow?
        # TODO: double hit? might be imba. but the other will hit back every time?

    type = models.PositiveSmallIntegerField("Type", choices=TypeChoices.choices, unique=True)

    def __str__(self) -> str:
        return self.get_type_display()
