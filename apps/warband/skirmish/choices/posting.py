from typing import Literal

from django.db import models


class PostingChoices(models.IntegerChoices):
    """
    Where a man of a war band stands while it is at home: the three places a raid can land.

    One per raid kind, which is what makes a posting mean something - a raid on the herds meets the men
    posted at the herds. The kind names its place in "RaidKind.POSTING".
    """

    HERDS = 1, "Herds"
    VILLAGE = 2, "Village"
    BURH = 3, "Burh"


# The order a war band's places are read out in: the burh first, because it is where every man stands
# who was never posted anywhere else, and the outlying places after it
POSTINGS_IN_DISPLAY_ORDER = (PostingChoices.BURH, PostingChoices.VILLAGE, PostingChoices.HERDS)

# Type hints
PostingTypeHint = Literal[*PostingChoices.values]
