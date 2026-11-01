from django.db import models


class MilestoneKindChoices(models.IntegerChoices):
    """
    What kind of moment in a man's life a milestone keeps.

    Only the moments nothing else in the game remembers. His fights, how each ended for him, whom he
    killed, his errands and his wounds are already rows of their own, and the story on his page reads
    them where they are - see "WarriorStory".
    """

    JOINED = 1, "Joined a war band"
    TOOK_SEAT = 2, "Took the seat of a fallen leader"
    NAMED = 3, "Earned an epithet"
    # A trait, unnamed: traits stay hidden until #313, so all a milestone keeps is that the fight made
    # something of him, which is what the month log already tells the player
    CHANGED = 4, "Came back from a fight a different man"


class JoinedWayChoices(models.IntegerChoices):
    """
    How a man came onto a roster. One per road the game has onto one.
    """

    FOUNDED = 1, "Led the war band from its first day"
    DRAFTED = 2, "Drafted from the fyrd"
    HIRED = 3, "Hired from the pub"
    SWORN_FROM_CELLS = 4, "Sworn in from the cells"
    ERRAND_REWARD = 5, "Came as an errand's reward"
    # A levy the fyrd raised when the seat fell empty with nobody left to take it. One milestone for both
    # halves of it, because joining and taking the seat were one moment for him
    RAISED_TO_LEAD = 6, "Raised by the fyrd to lead"
