from django.db import models


class TurningPointChoices(models.IntegerChoices):
    """
    A moment in a fight that stops it and waits for the player's word.

    Numbered in the order a round that brings several of them shows them: only the most important one
    becomes the stop, so the lowest value wins - see "TurningPointService".
    """

    # The player's leader has lost half his health and is still on his feet
    LEADER_THREATENED = 1, "Leader threatened"
    # One or more of the player's men went down this round: knocked out, killed or fled
    MAN_DOWN = 2, "Man down"
    # The enemy leader has lost half his health and is still on his feet
    ENEMY_LEADER_EXPOSED = 3, "Enemy leader exposed"
