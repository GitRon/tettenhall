from django.db import models


class BlowOutcomeChoices(models.IntegerChoices):
    """
    How one exchange ended, which the damage alone cannot say.

    Three of these four are recorded as zero damage today and are not the same thing at all: a swing
    that went wide, an action that threw nothing, and armour that took the whole blow. Separating
    them is what lets a count of "blows landed" mean anything.
    """

    OUTCOME_HIT = 1, "Hit"
    OUTCOME_ABSORBED = 2, "Absorbed"
    OUTCOME_MISSED = 3, "Missed"
    OUTCOME_NOT_THROWN = 4, "Not thrown"
