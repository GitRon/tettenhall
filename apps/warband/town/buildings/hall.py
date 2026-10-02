from apps.warband.town.buildings.base import Building, BuildingEffect


class Hall(Building):
    """
    Drives the monthly building income, how many mercenaries the pub holds and how many prisoners the
    cells keep.

    Every level pays for itself within a campaign, for the men it asks for: the Great Hall in about
    three months, the High Hall in about eight. What a level costs is the months its war band goes
    without the men and gear that silver would have bought, which is a choice a faction has to make.

    A level pays its revenue in full only to a faction keeping the men it asks for, and the men it
    asks for are the mercenary slots it opens: the hall that holds three is the hall that needs
    three. Below that it pays a share, never less than the baseline a town earns with no hall at all.

    It is also where the war band feasts, once a month and all of it at once. The level decides how
    much of a cut ceiling a feast gives back - a share of the ceiling a man holds now, mended toward
    the highest he ever held and never past it - and a town with no hall cannot feast at all. That
    makes the larger halls the repair for a broken nerve as well as the income.

    The feast is priced per head, not per point mended: the whole roster sits down to eat, so the
    roster is what it costs. A man already whole is fed and charged for all the same, which is why the
    price is small - the silver is meant to go on a war band that has actually been hurt.

    The cells are the hall's as well, because a lord kept the men he took under his own roof. A capture
    is never refused for want of room - a man carried off the field senseless has no say in it - but
    the places decide how many are still there when the month turns: the ones held out in the open
    slip away over its nights. That caps the stock of trained men a war band can sit on, not how many
    it takes in, which is why a level adds a single place.
    """

    BUILDING_NAME = "hall"
    BUILDING_LABEL = "Hall"

    REVENUE_PER_ROUND = 0
    AVAILABLE_MERCENARIES = 0
    WARRIORS_FOR_FULL_REVENUE = 0
    CELL_PLACES = 0
    # Zero is "this hall cannot feast", not "a feast that mends nothing"
    FEAST_RESTORED_SHARE = 0.0
    FEAST_PRICE_PER_HEAD = 15

    BUILDING_COSTS = 0

    @classmethod
    def get_levels(cls) -> tuple[type[Building], ...]:
        return (NoHall, SmallHall, MediumHall, LargeHall)

    @classmethod
    def get_effects(cls) -> tuple[BuildingEffect, ...]:
        return (
            BuildingEffect(label="Monthly income", value=f"{cls.REVENUE_PER_ROUND} silver"),
            BuildingEffect(label="Men needed for full income", value=str(cls.WARRIORS_FOR_FULL_REVENUE)),
            BuildingEffect(label="Mercenaries in the pub", value=str(cls.AVAILABLE_MERCENARIES)),
            BuildingEffect(label="Prisoners the cells hold", value=str(cls.CELL_PLACES)),
            BuildingEffect(
                label="A feast mends a cut ceiling by",
                value=f"{round(cls.FEAST_RESTORED_SHARE * 100)}%" if cls.can_feast() else "No feasts",
            ),
            BuildingEffect(label="Feast per man", value=f"{cls.FEAST_PRICE_PER_HEAD} silver"),
        )

    @classmethod
    def can_feast(cls) -> bool:
        return cls.FEAST_RESTORED_SHARE > 0

    @classmethod
    def get_feast_price(cls, *, head_count: int) -> int:
        return cls.FEAST_PRICE_PER_HEAD * head_count

    @classmethod
    def get_revenue_for_war_band(cls, *, warriors_on_payroll: int) -> int:
        """
        What this level pays a faction keeping "warriors_on_payroll" men.

        The count is the men drawing a wage, which leaves the leader out by construction - he is off
        the payroll because he is bought by nobody - so a faction whose roster is its leader alone
        earns the baseline whatever it has built. That is the point of the rule: the town is held by
        the men paid to hold it, and a hall bought in month one against a war band of nobody is an
        annuity the game charges nothing for.

        The floor is the level-0 variant's revenue rather than zero. A town keeps trickling in what a
        hall-less one earns, so an under-manned hall is an investment that has not paid off yet and
        never a town that starves.
        """
        if cls.WARRIORS_FOR_FULL_REVENUE == 0:
            return cls.REVENUE_PER_ROUND

        manned_share = min(1, warriors_on_payroll / cls.WARRIORS_FOR_FULL_REVENUE)

        return max(cls.get_levels()[0].REVENUE_PER_ROUND, round(cls.REVENUE_PER_ROUND * manned_share))


class NoHall(Hall):
    REVENUE_PER_ROUND = 50
    AVAILABLE_MERCENARIES = 1
    WARRIORS_FOR_FULL_REVENUE = 0
    # One, not none: level 0 is a baseline, and a single place keeps the one prisoner that matters
    # most - a rival's captured leader - over the month without any building at all
    CELL_PLACES = 1

    FEAST_RESTORED_SHARE = 0.0

    BUILDING_COSTS = 0


class SmallHall(Hall):
    REVENUE_PER_ROUND = 300
    AVAILABLE_MERCENARIES = 1
    WARRIORS_FOR_FULL_REVENUE = 1
    CELL_PLACES = 2

    FEAST_RESTORED_SHARE = 0.1

    BUILDING_COSTS = 600


class MediumHall(Hall):
    REVENUE_PER_ROUND = 550
    AVAILABLE_MERCENARIES = 2
    WARRIORS_FOR_FULL_REVENUE = 2
    CELL_PLACES = 3

    FEAST_RESTORED_SHARE = 0.2

    BUILDING_COSTS = 800


class LargeHall(Hall):
    REVENUE_PER_ROUND = 750
    AVAILABLE_MERCENARIES = 3
    WARRIORS_FOR_FULL_REVENUE = 3
    CELL_PLACES = 4

    FEAST_RESTORED_SHARE = 0.3

    BUILDING_COSTS = 1600
