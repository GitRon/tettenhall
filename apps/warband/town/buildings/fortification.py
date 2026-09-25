from apps.warband.town.buildings.base import Building, BuildingEffect


class Fortification(Building):
    """
    Sets the wall a war band marching on this town has to break before the defenders lose its cover.

    The strength is what the skirmish staged by the march opens with, and a level is what the wall is
    worth every time rather than a stock that is spent: whatever a fight batters down stands again for
    the next one. With two men on it the three levels take about 2.5, 4.4 and 6.3 rounds to break, and
    from roughly 45 points upward storming stops being the faster way in - so the top level is a wall
    nobody can shortcut rather than a bigger version of the first.

    The only lever of the five whose level 0 is no effect at all: a town without a wall is fought in the
    open, with no cover to break and no defence bonus for the men behind it.
    """

    BUILDING_NAME = "fortification"
    BUILDING_LABEL = "Fortification"

    FORTIFICATION_STRENGTH = 0

    BUILDING_COSTS = 0

    @classmethod
    def get_levels(cls) -> tuple[type[Building], ...]:
        return (NoFortification, Palisade, Earthwork, BurhWall)

    @classmethod
    def get_effects(cls) -> tuple[BuildingEffect, ...]:
        return (BuildingEffect(label="Wall strength when marched on", value=f"{cls.FORTIFICATION_STRENGTH} points"),)


class NoFortification(Fortification):
    FORTIFICATION_STRENGTH = 0

    BUILDING_COSTS = 0


class Palisade(Fortification):
    FORTIFICATION_STRENGTH = 20

    BUILDING_COSTS = 500


class Earthwork(Fortification):
    FORTIFICATION_STRENGTH = 35

    BUILDING_COSTS = 1750


class BurhWall(Fortification):
    FORTIFICATION_STRENGTH = 50

    BUILDING_COSTS = 3500


# Where a faction the player did not create starts, and stays: nothing upgrades a rival's town, so this
# is the wall the player meets at every rival's gate for the whole savegame. Two men break the Palisade
# in about two and a half rounds, so an early war band pays for the march without being stopped by it.
# Read off get_levels() rather than written as a number, so it keeps naming the Palisade if a level is
# inserted.
NPC_STARTING_FORTIFICATION_LEVEL: int = Fortification.get_levels().index(Palisade)
