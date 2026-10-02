from typing import Literal

from django.db import models


class RaidKindChoices(models.IntegerChoices):
    """
    What a war band sets out to take when it marches on a rival.

    The stored value only. What each kind does to the fight and what a victory takes lives on its class
    in "apps.warband.skirmish.raids", which [get_raid_kind] reads back from this value.
    """

    LIFT_THE_HERDS = 1, "Lift the herds"
    BURN_THE_VILLAGE = 2, "Burn the village"
    STORM_THE_BURH = 3, "Storm the burh"


# Type hints
RaidKindTypeHint = Literal[*RaidKindChoices.values]
