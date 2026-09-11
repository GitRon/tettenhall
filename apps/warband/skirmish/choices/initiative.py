from django.db import models


class InitiativeChoices(models.IntegerChoices):
    """
    How a warrior came to be the attacker, which the pairing alone cannot say.

    Two paths raise "AttackerDefenderDecided" and they are not the same thing at all: one man was
    quicker than the man facing him, and one man had nobody to face. Separating them is what lets the
    battle log name a cause instead of stating the outcome twice.
    """

    INITIATIVE_WON_THE_ROLL = 1, "Won the roll"
    INITIATIVE_UNOPPOSED = 2, "Unopposed"
