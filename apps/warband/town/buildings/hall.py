from apps.warband.town.buildings.base import Building, BuildingEffect


class Hall(Building):
    """
    Drives the monthly building income and how many mercenaries the pub holds.

    Revenue grows by less than the costs do, so the largest hall never pays for itself out of income
    alone - what justifies it is the third mercenary slot.

    A level pays its revenue in full only to a faction keeping the men it asks for, and the men it
    asks for are the mercenary slots it opens: the hall that holds three is the hall that needs
    three. Below that it pays a share, never less than the baseline a town earns with no hall at all.
    """

    BUILDING_NAME = "hall"
    BUILDING_LABEL = "Hall"

    REVENUE_PER_ROUND = 0
    AVAILABLE_MERCENARIES = 0
    WARRIORS_FOR_FULL_REVENUE = 0

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
        )

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

    BUILDING_COSTS = 0


class SmallHall(Hall):
    REVENUE_PER_ROUND = 300
    AVAILABLE_MERCENARIES = 1
    WARRIORS_FOR_FULL_REVENUE = 1

    BUILDING_COSTS = 900


class MediumHall(Hall):
    REVENUE_PER_ROUND = 550
    AVAILABLE_MERCENARIES = 2
    WARRIORS_FOR_FULL_REVENUE = 2

    BUILDING_COSTS = 2100


class LargeHall(Hall):
    REVENUE_PER_ROUND = 750
    AVAILABLE_MERCENARIES = 3
    WARRIORS_FOR_FULL_REVENUE = 3

    BUILDING_COSTS = 4200
