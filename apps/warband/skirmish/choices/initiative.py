from django.db import models


class InitiativeChoices(models.IntegerChoices):
    """
    How a warrior came to be striking this blow, which the pairing alone cannot say.

    Two paths raise "AttackerDefenderDecided" and they are not the same thing at all: one man was
    quicker than the man facing him and strikes first, and one man had nobody to face. The third is
    the blow the slower man of a pair swings back once the first has landed. Separating them is what
    lets the battle log name a cause instead of stating the outcome twice.
    """

    INITIATIVE_WON_THE_ROLL = 1, "Won the roll"
    INITIATIVE_UNOPPOSED = 2, "Unopposed"
    INITIATIVE_COUNTER = 3, "Struck back"
