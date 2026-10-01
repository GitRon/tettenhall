class CalendarMonth:
    """
    One month of the Anglo-Saxon year, with everything that month does to the game.

    The months come in two seasons, the way Bede has them in *De temporum ratione*: a season class
    ([Summer], [Winter]) sets the numbers every month of it shares, and a month class subclasses its
    season and overrides only what sets it apart. So a season is changed in one place, and a special
    month is a class with one or two constants in it.

    The rules and the page read the same class: the handlers take their numbers from the constants,
    and [get_effects] words them for the player - so what the dashboard says a month does and what
    the month does cannot drift apart.

    Classes rather than instances, like the town's buildings and the month's incidents, which is why
    "do_not_call_in_templates" is set: a template would otherwise call the class and render the
    instance it built.
    """

    do_not_call_in_templates = True

    # The month's own name, in Old English, and the season it belongs to, in English. The page shows
    # them side by side: "Haligmonath · Summer"
    NAME = ""
    SEASON = ""

    # Silver owed per warrior sent against a rival
    MARCH_COST_PER_WARRIOR = 0
    # Multiplies a warrior's monthly training improvement before it is rounded and floored at 1
    TRAINING_FACTOR = 1.0
    # Silver every faction takes in when the month begins
    HARVEST_SILVER = 0
    # Whether the fyrd reserve grows this month at all
    FYRD_REPLENISHES = True

    @classmethod
    def get_march_cost(cls, *, warrior_count: int) -> int:
        """What sending "warrior_count" men against a rival costs this month."""
        return cls.MARCH_COST_PER_WARRIOR * warrior_count

    @classmethod
    def get_effects(cls) -> tuple[str, ...]:
        """
        One line per effect in force this month, season and month together, in display order.

        Read off the constants, so a month that changes a number describes itself. A month that
        levers nothing - a plain summer month - has no lines at all, and each page decides for itself
        whether that is worth saying.
        """
        effects = []
        if cls.MARCH_COST_PER_WARRIOR:
            effects.append(f"Winter march: {cls.MARCH_COST_PER_WARRIOR} silver per man")
        if cls.TRAINING_FACTOR > 1:
            effects.append("Training advances faster")
        if cls.HARVEST_SILVER:
            effects.append(f"The harvest brings in {cls.HARVEST_SILVER} silver")
        if not cls.FYRD_REPLENISHES:
            effects.append("The fyrd does not grow: its men are in the fields")
        return tuple(effects)
