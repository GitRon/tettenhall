import random

from apps.faction.models.faction import Faction
from apps.quest.models.quest import Quest
from apps.savegame.models.savegame import Savegame


class QuestGenerator:
    savegame: Savegame

    def __init__(self, *, savegame: Savegame) -> None:
        super().__init__()

        self.savegame = savegame

    def process(self) -> Quest | None:
        # A savegame without these is degenerate - bootstrapping always creates a player faction and
        # three to five rivals - so say so instead of dying on an IndexError further down
        if self.savegame.player_faction_id is None:
            raise RuntimeError(f"Savegame {self.savegame.id} has no player faction to create a quest for.")

        if (
            not Faction.objects.still_in_play(savegame_id=self.savegame.id)
            .exclude(id=self.savegame.player_faction_id)
            .exists()
        ):
            raise RuntimeError(f"Savegame {self.savegame.id} has no rival faction a quest could target.")

        # The same queryset the attack path resolves its target with, so the two paths cannot
        # disagree about who may be marched on: a faction with nobody healthy left to defend it is
        # no longer somewhere to send a warband, because the errand would stage a fight against an
        # empty side. That a beaten enemy becomes unreachable at all is wrong and #44 owns it; this
        # only stops the quest path walking into the hole the attack path already guards.
        target_faction_list = list(
            Faction.objects.attackable_targets(
                player_faction=self.savegame.player_faction, month=self.savegame.current_month
            )
        )

        # Rivals are left, but every one of them has been flattened. No quest this month rather than
        # an exception: the month advance is what asks for one, and a player who has just beaten his
        # last standing opponent has not broken the game. They are back on the board as soon as the
        # monthly healing puts a warrior back on his feet.
        if not target_faction_list:
            return None

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
