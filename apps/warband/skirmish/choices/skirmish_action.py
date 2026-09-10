from typing import Literal

from django.db import models


class SkirmishActionChoices(models.IntegerChoices):
    SIMPLE_ATTACK = 1, "Simple attack"
    RISKY_ATTACK = 2, "Risky attack"
    FAST_ATTACK = 3, "Fast attack"
    DEFENSIVE_STANCE = 4, "Defensive stance"
    # The one action that takes a warrior off the field instead of doing something on it. It is
    # answered at the start of the round, before anybody is paired, so it never reaches
    # "get_service_by_attack_action" and has no service of its own
    FLEE = 5, "Flee"


# Type hints
SkirmishActionTypeHint = Literal[*SkirmishActionChoices.values]
