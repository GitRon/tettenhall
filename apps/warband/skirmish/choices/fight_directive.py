from django.db import models


class FightDirectiveChoices(models.IntegerChoices):
    """
    What the player tells his men for the next round instead of ordering each one by hand.

    Every directive lasts a single round; the round after it, the men decide for themselves again.
    """

    # Nothing to say: every man decides as a rival's men do
    FIGHT_ON = 1, "Fight on"
    # The leader steadies the side
    RALLY = 2, "Rally"
    # Every man leaves the field
    SOUND_THE_RETREAT = 3, "Sound the retreat"
    # The leader stops trading blows and guards himself
    HOLD_BACK = 4, "Hold back"
    # The leader leaves the field, alone
    LEAVE_THE_FIELD = 5, "Leave the field"
    # Every man swings hard
    PRESS_THE_ATTACK = 6, "Press the attack"
