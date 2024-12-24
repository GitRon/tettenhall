from apps.skirmish.models.skirmish import Skirmish


class BaseSkirmishGenerator:
    warriors_faction_1: list
    warriors_faction_2: list

    def __init__(self, *, warriors_faction_1: list, warriors_faction_2: list) -> None:
        # todo refactor that i can pass a list and generate opponents or just create random opponents
        super().__init__()

        self.warriors_faction_1 = warriors_faction_1
        self.warriors_faction_2 = warriors_faction_2

    def process(self):
        skirmish = Skirmish.objects.create(
            name="New Battle",
            player_faction_id=2,
            non_player_faction_id=1,
        )

        skirmish.player_warriors.add(*self.warriors_faction_1)
        skirmish.non_player_warriors.add(*self.warriors_faction_2)

        return skirmish
