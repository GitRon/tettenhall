from apps.warband.calendar.months.base import CalendarMonth


class Winter(CalendarMonth):
    """
    Winterfylleth to Hreðmonath: war is dear and the men drill indoors.

    Winter does not forbid marching and does not touch healing or building. It prices a march and
    speeds training, which is what gives the player a reason to take a town before Winterfylleth and
    to save silver for the months after it.
    """

    SEASON = "Winter"

    # A man's wage is half his recruitment price, whose base roll centres on 100, so about 50 silver a
    # month. An easy quest pays 150-350 for a full band: five men marching cost 50, about a fifth of
    # it - felt, not blocking
    MARCH_COST_PER_WARRIOR = 10
    # The mean improvement is 15 a month against 100 per level. One winter of six months gives about
    # 135 progress instead of 90: an extra level every second winter
    TRAINING_FACTOR = 1.5


class Winterfylleth(Winter):
    NAME = "Winterfylleth"


class Blotmonath(Winter):
    """The slaughter month: stores are laid in, so a march costs less than in the rest of the winter."""

    NAME = "Blotmonath"

    # Half the winter cost
    MARCH_COST_PER_WARRIOR = 5


class AerraGeola(Winter):
    """Before Yule: the feast calls the men home, so a march costs more than in the rest of the winter."""

    NAME = "Ærra Geola"

    # One and a half times the winter cost
    MARCH_COST_PER_WARRIOR = 15


class AefterraGeola(Winter):
    """After Yule, and the first month of the year: the march costs what it did before the feast."""

    NAME = "Æfterra Geola"

    # One and a half times the winter cost, as in Ærra Geola
    MARCH_COST_PER_WARRIOR = 15


class Solmonath(Winter):
    NAME = "Solmonath"


class Hredmonath(Winter):
    NAME = "Hreðmonath"
