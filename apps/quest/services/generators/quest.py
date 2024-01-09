import random

from apps.faction.models.faction import Faction
from apps.quest.models.quest import Quest


class QuestGenerator:
    def process(self) -> Quest:
        faction_qs = Faction.objects.exclude(id=1).values_list("id", flat=True)

        quest_name_list = (
            "Hunt down raiders",
            "Pillage village",
            "Avenge lost villager lives",
            "Raid cattle",
        )

        name = random.choice(quest_name_list)
        faction_id = random.choice(faction_qs)
        difficulty = random.choice(Quest.DifficultyChoices.choices)

        return Quest.objects.create(name=name, faction_id=faction_id, difficulty=difficulty[0])
