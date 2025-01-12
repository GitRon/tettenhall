from typing import Literal

from django.db import models


class SkirmishActionChoices(models.IntegerChoices):
    SIMPLE_ATTACK = 1, "Simple attack"
    RISKY_ATTACK = 2, "Risky attack"
    FAST_ATTACK = 3, "Fast attack"
    DEFENSIVE_STANCE = 4, "Defensive stance"
    # TODO: provide attack to incapacitate warriors more likely
    # TODO: do we want that the defender can retaliate after the attacker has hit him?
    #  -> might be a new attack action for higher levels like in battle brothers?


# Type hints
SkirmishActionTypeHint = Literal[*SkirmishActionChoices.values]
