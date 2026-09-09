class OccupationSpoils:
    """
    What riding into an undefended town is worth.

    Strictly less than a won battle, and that is the point: there is no fight, so there is no spoil
    beyond what the town itself holds. No gear and no rank-and-file prisoners either - the survivors
    routed and took their kit with them, the same distinction "handle_faction_wins_skirmish" draws
    between a man left lying on the field and one who walked off it.

    A share rather than a flat purse because a rival's treasury is a moving number now: it takes an
    income of its own every month and pays for a roster it may no longer be able to field, so a purse
    grows while the rival is winning and drains once he has been beaten. See [RivalIncome]. Half of
    it makes the timing of the ride worth thinking about without turning one broken war band into the
    silver for the rest of the savegame.

    The lever is here rather than in the handler for the same reason "apps/town/buildings/" owns the
    player's numbers: a game-balance number gets one home.
    """

    PLUNDERED_TREASURY_SHARE = 0.5

    @classmethod
    def get_plundered_silver(cls, *, treasury: int) -> int:
        # A faction can be in the red - the salary run bills whether or not there is silver for it -
        # and half a debt is not something to carry home. Nothing is taken then, and nothing is owed
        # to the town either.
        return max(0, round(treasury * cls.PLUNDERED_TREASURY_SHARE))
