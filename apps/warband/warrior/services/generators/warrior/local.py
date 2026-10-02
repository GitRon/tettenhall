from apps.warband.warrior.services.generators.warrior.fyrd import FyrdWarriorGenerator


class LocalWarriorGenerator(FyrdWarriorGenerator):
    """
    A man of the place a raid lands on - a herdsman, a villager, a man of the burh's fyrd - who turns out
    to defend it for one fight and goes home afterwards.

    The fyrd's archetype, because he is the same kind of man, with less nerve: he is defending his own
    door rather than marching under a banner. He is nobody's hire, so he draws no wage.
    """

    MORALE_MU = 4
    MORALE_SIGMA = 2

    draws_a_wage = False
