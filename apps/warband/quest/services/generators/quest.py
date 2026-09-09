import random

from apps.warband.faction.models.faction import Faction
from apps.warband.quest.models.quest import Quest
from apps.warband.quest.models.quest_name import QuestName
from apps.warband.savegame.models.savegame import Savegame
from apps.warband.skirmish.models.warrior import Warrior


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

        # Rivals are left, but not one of them can field a defender - every man beaten, or every man
        # already in a fight. Only the first is reachable from here, since nothing is committed yet
        # when the month is being prepared, but the branch answers both. No quest this month rather
        # than an exception: the month advance is what asks for one, and a player who has just beaten
        # his last standing opponent has not broken the game. They are back on the board as soon as
        # the monthly healing puts a warrior back on his feet.
        if not target_faction_list:
            return None

        quest_name_list = list(QuestName.objects.all())

        if not quest_name_list:
            raise RuntimeError(
                "There are no quest names to draw from. "
                "Load the reference data with 'loaddata culture itemtype questname'."
            )

        name = random.choice(quest_name_list).name
        target_faction = random.choice(target_faction_list)
        difficulty = random.choice(Quest.DifficultyChoices.choices)

        quest = Quest(name=name, target_faction=target_faction, difficulty=difficulty[0])
        quest.expected_opposition = self._expected_opposition(quest=quest)
        quest.loot = quest.calculate_loot()
        quest.save()

        return quest

    def _expected_opposition(self, *, quest: Quest) -> int:
        """
        How big a war band this quest can honestly be written against.

        The band's top or the target's roster, whichever runs out first. A rival opens a savegame
        with a single warrior and gains at most one a month, so for the first several months the top
        of either band is out of reach - and a purse measured against a number nobody can field is a
        purse that is never paid.

        Counted the way "_muster_defenders" musters, because that is who will actually turn out:
        healthy, this faction's, and not already committed to a fight. Never zero, because
        "attackable_targets" has already established that the chosen target can field a defender.
        """
        _, band_maximum = quest.get_min_max_number_of_opponents()
        musterable_warriors = (
            Warrior.objects.filter_healthy()
            .filter_faction(faction_id=quest.target_faction_id)
            .exclude_currently_busy(month=self.savegame.current_month)
            .count()
        )

        return min(band_maximum, musterable_warriors)
