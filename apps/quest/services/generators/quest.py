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
        # A savegame without these is degenerate - bootstrapping always creates a player faction and
        # three to five rivals - so say so instead of dying on an IndexError further down
        if self.savegame.player_faction_id is None:
            raise RuntimeError(f"Savegame {self.savegame.id} has no player faction to create a quest for.")

        target_faction_list = list(
            Faction.objects.filter(savegame=self.savegame).exclude(id=self.savegame.player_faction_id)
        )
        if not target_faction_list:
            raise RuntimeError(f"Savegame {self.savegame.id} has no rival faction a quest could target.")

        # TODO: move to model?
        quest_name_list = (
            "Hunt down raiders",
            "Pillage village",
            "Avenge lost villager lives",
            "Raid cattle",
        )

        name = random.choice(quest_name_list)
        target_faction = random.choice(target_faction_list)
        difficulty = random.choice(Quest.DifficultyChoices.choices)

        quest = Quest(name=name, target_faction=target_faction, difficulty=difficulty[0])
        quest.loot = quest.calculate_loot()
        quest.save()

        return quest
