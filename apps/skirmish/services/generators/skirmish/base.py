from apps.skirmish.models.skirmish import Skirmish


class BaseSkirmishGenerator:
    name: str
    warriors_faction_1: list
    warriors_faction_2: list

    def __init__(self, *, name: str, warriors_faction_1: list, warriors_faction_2: list) -> None:
        super().__init__()

        self.name = name
        self.warriors_faction_1 = warriors_faction_1
        self.warriors_faction_2 = warriors_faction_2

    def process(self) -> Skirmish:
        skirmish = Skirmish.objects.create(
            name=self.name,
            player_faction_id=self.warriors_faction_1[0].faction.id,
            non_player_faction_id=self.warriors_faction_2[0].faction.id,
        )

        skirmish.player_warriors.add(*self.warriors_faction_1)
        skirmish.non_player_warriors.add(*self.warriors_faction_2)

        return skirmish
