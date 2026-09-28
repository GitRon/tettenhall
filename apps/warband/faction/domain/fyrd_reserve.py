import random


class FyrdReserve:
    """
    How many levies a faction has to draft from, at the start and as the months turn.

    The reserve is the brake on a rival's growth rather than its purse - a draft is free - so these two
    rolls decide how fast a war band can refill itself. Each is its own method so that a test can fix
    one without handing the other a value it could never produce.
    """

    STARTING_RESERVE_MIN = 2
    STARTING_RESERVE_MAX = 5

    # A month that sends anybody sends at most this many, and it may send nobody
    MONTHLY_RECRUITS_MAX = 2

    @classmethod
    def roll_starting_reserve(cls) -> int:
        return random.randint(cls.STARTING_RESERVE_MIN, cls.STARTING_RESERVE_MAX)

    @classmethod
    def roll_monthly_recruits(cls) -> int:
        return random.randrange(0, cls.MONTHLY_RECRUITS_MAX + 1)
