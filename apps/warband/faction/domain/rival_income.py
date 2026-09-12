class RivalIncome:
    """
    What a faction with no player behind it earns when a month turns.

    A rival has an income of its own rather than the player's building revenue. It is pinned to
    "NoHall" - its town is created at every default and nothing ever builds one up - so the town
    would pay it a flat 50 silver however large its war band grew, and a single fyrd levy already
    costs more than that.

    So it scales with the roster, and on the *healthy* part of it deliberately, while the wage bill
    covers everybody who is not dead. A faction that cannot field a warrior should not be earning off
    him. The two rosters differing is the pressure, not a miscount: the surplus narrows as warriors
    level up and their salaries grow with them, and it inverts once a faction has been beaten - which
    is what makes beating one mean something between one battle and the next.

    **The player is counted differently on purpose**, over the men he pays rather than the men he can
    field (see "Hall.get_revenue_for_war_band"). The two incomes are different things: a rival's
    income *is* its war band, out in the field earning, so a man who cannot march earns nothing. The
    player's is a town's trade, held by the men on his payroll, and a wounded man he is still paying
    still holds it. Counting the player's wounded against him too would put the cost of a lost
    skirmish on his income as well as on his wages and his sanctuary - a compounding penalty on the
    player who fights, which is the opposite of what the rule is for (#192).

    The levers are here rather than in the handler for the same reason "apps/town/buildings/" owns the
    player's: a game-balance number gets one home.
    """

    # A fyrd levy's salary lands around 90, so a warrior brings in roughly 110 more than he costs at
    # level 1. The fyrd reserve is the brake on a rival's growth rather than its purse, which is the
    # shape "handle_replenish_fyrd_reserve" was already built to be - a rival grows by drafting, and
    # a draft is free. What the surplus decides is how long it takes for levelling to eat it: every
    # level adds a tenth to a salary, so the men a rival keeps alive turn from an income into a bill
    # on their own.
    BASE_REVENUE_PER_MONTH = 50
    REVENUE_PER_HEALTHY_WARRIOR = 200

    @classmethod
    def get_monthly_income(cls, *, healthy_warriors: int) -> int:
        return cls.BASE_REVENUE_PER_MONTH + cls.REVENUE_PER_HEALTHY_WARRIOR * healthy_warriors
