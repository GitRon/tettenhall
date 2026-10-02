from apps.warband.item.services.generators.item.mercenary import MercenaryItemGenerator
from apps.warband.warrior.services.generators.warrior.base import BaseWarriorGenerator


class ChampionWarriorGenerator(BaseWarriorGenerator):
    """
    A fighter of name, fetched home by a quest rather than hired off a bench.

    Drawn above the mercenary on every axis, because a quest that brings back a man the pub would sell
    is a slower pub. He is priced off the same yardsticks as anyone else, so his wage is a mercenary's
    and then some - which is what a quest fetching him has to be worth against.
    """

    XP_MU = 250
    XP_SIGMA = 75
    HEALTH_MU = 50
    HEALTH_SIGMA = 12
    MORALE_MU = 13
    MORALE_SIGMA = 4
    STATS_MU = 14
    STATS_SIGMA = 3
    STATS_MIN = 8
    PROGRESS_MU = 50
    PROGRESS_SIGMA = 50

    item_generator_class = MercenaryItemGenerator
    chance_for_weapon = 1.0
    chance_for_armor = 0.5
