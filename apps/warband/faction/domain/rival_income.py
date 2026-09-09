class RivalIncome:
    """
    What a faction with no player behind it earns when a month turns.

    A rival has an income of its own rather than the player's building revenue. Hall revenue is flat
    per level while a wage bill scales with the roster, so routing rivals through the town would move
    the constant and never the slope: a rival is pinned to "NoHall" - its town is created at every
    default - and a single leader already costs more than that level pays.

    So it scales with the roster too, and on the *healthy* part of it deliberately, while the wage
    bill covers everybody who is not dead. A faction that cannot field a warrior should not be
    earning off him. The two rosters differing is the pressure, not a miscount: the surplus narrows as
    warriors level up and their salaries grow with them, and it inverts once a faction has been beaten
    - which is what makes beating one mean something between one battle and the next.

    The levers are here rather than in the handler for the same reason "apps/town/buildings/" owns the
    player's: a game-balance number gets one home.
    """

    # A fyrd levy's salary lands around 150, so a warrior brings in roughly 50 more than he costs at
    # level 1. A rival therefore accumulates slowly and the fyrd reserve stays the real brake on its
    # growth, which is the shape "handle_replenish_fyrd_reserve" was already built to be.
    BASE_REVENUE_PER_MONTH = 50
    REVENUE_PER_HEALTHY_WARRIOR = 200

    @classmethod
    def get_monthly_income(cls, *, healthy_warriors: int) -> int:
        return cls.BASE_REVENUE_PER_MONTH + cls.REVENUE_PER_HEALTHY_WARRIOR * healthy_warriors
