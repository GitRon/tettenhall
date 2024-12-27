import random

from apps.faction.models.faction import Faction
from apps.quest.models.quest import Quest
from apps.savegame.models.savegame import Savegame


class QuestGenerator:
    savegame: Savegame

    def __init__(self, *, savegame: Savegame) -> None:
        super().__init__()

        self.savegame = savegame

    def process(self) -> Quest:
        faction_qs = Faction.objects.filter(savegame=self.savegame).exclude(id=self.savegame.player_faction.id)

        # TODO: move to model?
        quest_name_list = (
            "Hunt down raiders",
            "Pillage village",
            "Avenge lost villager lives",
            "Raid cattle",
        )

        name = random.choice(quest_name_list)
        target_faction = random.choice(faction_qs)
        difficulty = random.choice(Quest.DifficultyChoices.choices)

        quest = Quest(name=name, target_faction=target_faction, difficulty=difficulty[0])
        quest.loot = quest.calculate_loot()
        quest.save()

        return quest
