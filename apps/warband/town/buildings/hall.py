from apps.warband.town.buildings.base import Building, BuildingEffect


class Hall(Building):
    """
    Drives the monthly building income and how many mercenaries the pub holds.

    Revenue grows by less than the costs do, so the largest hall never pays for itself out of income
    alone - what justifies it is the third mercenary slot.

    A level pays its revenue in full only to a faction keeping the men it asks for, and the men it
    asks for are the mercenary slots it opens: the hall that holds three is the hall that needs
    three. Below that it pays a share, never less than the baseline a town earns with no hall at all.

    It is also where the war band feasts, once a month and all of it at once. The level decides how
    much of a cut ceiling a feast gives back - a share of the ceiling a man holds now, mended toward
    the highest he ever held and never past it - and a town with no hall cannot feast at all. That
    makes the larger halls the repair for a broken nerve as well as the income, which is the reason to
    build the one income alone never pays for.

    The feast is priced per head, not per point mended: the whole roster sits down to eat, so the
    roster is what it costs. A man already whole is fed and charged for all the same, which is why the
    price is small - the silver is meant to go on a war band that has actually been hurt.
    """

    BUILDING_NAME = "hall"
    BUILDING_LABEL = "Hall"

    REVENUE_PER_ROUND = 0
    AVAILABLE_MERCENARIES = 0
    WARRIORS_FOR_FULL_REVENUE = 0
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

    FEAST_RESTORED_SHARE = 0.0

    BUILDING_COSTS = 0


class SmallHall(Hall):
    REVENUE_PER_ROUND = 300
    AVAILABLE_MERCENARIES = 1
    WARRIORS_FOR_FULL_REVENUE = 1

    FEAST_RESTORED_SHARE = 0.1

    BUILDING_COSTS = 600


class MediumHall(Hall):
    REVENUE_PER_ROUND = 550
    AVAILABLE_MERCENARIES = 2
    WARRIORS_FOR_FULL_REVENUE = 2

    FEAST_RESTORED_SHARE = 0.2

    BUILDING_COSTS = 2100


class LargeHall(Hall):
    REVENUE_PER_ROUND = 750
    AVAILABLE_MERCENARIES = 3
    WARRIORS_FOR_FULL_REVENUE = 3

    FEAST_RESTORED_SHARE = 0.3

    BUILDING_COSTS = 4200
