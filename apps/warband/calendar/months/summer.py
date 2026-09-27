from apps.warband.calendar.months.base import CalendarMonth


class Summer(CalendarMonth):
    """
    Eosturmonath to Haligmonath: the campaigning season.

    Marching costs nothing and training goes at its ordinary pace, so summer is the baseline every
    winter number is measured against.
    """

    SEASON = "Summer"


class Eosturmonath(Summer):
    NAME = "Eosturmonath"


class Thrimilcemonath(Summer):
    NAME = "Þrimilcemonath"


class AerraLitha(Summer):
    NAME = "Ærra Liða"


class AefterraLitha(Summer):
    NAME = "Æfterra Liða"


class Weodmonath(Summer):
    NAME = "Weodmonath"


class Haligmonath(Summer):
    """
    The harvest month: silver comes in, and the fyrd does not grow because its men are in the fields.
    """

    NAME = "Haligmonath"

    # Below the smallest quest purse (150 silver for an easy one), so it is a cushion before the
    # winter rather than a substitute for marching
    HARVEST_SILVER = 100
    FYRD_REPLENISHES = False
