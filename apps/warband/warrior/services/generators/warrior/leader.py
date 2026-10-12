from apps.warband.item.services.generators.item.leader import LeaderItemGenerator
from apps.warband.warrior.services.generators.warrior.base import BaseWarriorGenerator


class LeaderWarriorGenerator(BaseWarriorGenerator):
    XP_MU = 100
    XP_SIGMA = 10
    HEALTH_MU = 40
    HEALTH_SIGMA = 10
    MORALE_MU = 10
    MORALE_SIGMA = 3
    STATS_MU = 8
    STATS_SIGMA = 3
    STATS_MIN = 4
    PROGRESS_MU = 50
    PROGRESS_SIGMA = 50

    item_generator_class = LeaderItemGenerator
    chance_for_weapon = 1
    chance_for_armor = 1

    # The player's own hand in the world rather than a hireling, so he is the one archetype off the
    # payroll - see "BaseWarriorGenerator.draws_a_wage"
    draws_a_wage = False

    def __init__(self, *, name: str | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.name = name

    def draw_name(self) -> str:
        # The one man the player may name himself. A typed name is taken as it stands, without the
        # living-names check a drawn one gets - see "handle_create_factions_for_new_savegame" for why
        # nobody can hold it before him
        if self.name is not None:
            return self.name

        return super().draw_name()
