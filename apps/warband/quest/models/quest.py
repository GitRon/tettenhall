import random

from django.db import models

from apps.warband.quest.managers.quest import QuestManager


class Quest(models.Model):
    class DifficultyChoices(models.IntegerChoices):
        DIFFICULTY_EASY = 1, "Easy"
        DIFFICULTY_HARD = 2, "Hard"

    name = models.CharField("Name", max_length=50)
    loot = models.PositiveSmallIntegerField("Loot (in silver)")
    target_faction = models.ForeignKey("warband.Faction", verbose_name="Target faction", on_delete=models.CASCADE)
    difficulty = models.PositiveSmallIntegerField("Difficulty", choices=DifficultyChoices.choices)
    expected_opposition = models.PositiveSmallIntegerField("Expected opposition")

    objects = QuestManager()

    class Meta:
        verbose_name = "Quest"
        verbose_name_plural = "Quests"
        default_related_name = "quests"

    def __str__(self) -> str:
        return self.name

    def get_min_max_number_of_opponents(self) -> (int, int):
        """
        How many of the target faction's warriors turn out, at the least and at the most.

        A selection size rather than a spawn count: the opposition is the rival's actual war band, so
        a faction with fewer men than the maximum simply fields what it has. Both ends are inclusive.

        The maximum is what a quest of this difficulty is worth at full price, which is why
        "expected_opposition" is capped by it and the purse is scaled against it - a target that
        cannot reach the top of the band signs a smaller contract rather than being paid a fraction
        of a larger one.
        """
        if self.difficulty == self.DifficultyChoices.DIFFICULTY_EASY:
            return 3, 5
        if self.difficulty == self.DifficultyChoices.DIFFICULTY_HARD:
            return 4, 8
        raise RuntimeError("Invalid difficulty choice.")

    def get_min_max_loot(self) -> (int, int):
        """
        What a quest of this difficulty pays for a full band, at the least and at the most.

        The one place the money per difficulty is written down, so the roll in "calculate_loot" and
        the average in "average_loot" cannot drift apart: the quest card obscures the figure against
        that average, and an average disagreeing with the range it obscures reports the same word for
        every quest.
        """
        if self.difficulty == self.DifficultyChoices.DIFFICULTY_EASY:
            return 150, 350
        if self.difficulty == self.DifficultyChoices.DIFFICULTY_HARD:
            return 250, 750
        raise RuntimeError("Invalid difficulty choice.")

    def _priced_for_expected_opposition(self, *, full_band_loot: int) -> int:
        """
        Brings a full-band figure down to the war band this quest was actually written against.

        A contract is priced when it is pinned to the board, not settled when it is resolved: the
        target's roster is what decides the size of the job, and a rival who can field one man is
        offering a one-man job at a one-man price. So the money follows the opposition here, once,
        and what the player accepted is then paid in full whatever turns out on the day.
        """
        _, band_maximum = self.get_min_max_number_of_opponents()

        return round(full_band_loot * self.expected_opposition / band_maximum)

    def calculate_loot(self) -> int:
        minimum_loot, maximum_loot = self.get_min_max_loot()

        return self._priced_for_expected_opposition(full_band_loot=random.randint(minimum_loot, maximum_loot))

    @property
    def average_loot(self) -> int:
        """
        What a quest like this one pays on average, for "obscurify" to describe the purse against.

        Derived from the same range and the same scaling the purse itself came out of, so the word on
        the card stays informative at every roster size instead of reading "Low" for every easy
        quest: a cap of five puts an easy quest's thresholds at 200 and 300, a cap of one puts them
        at 40 and 60, and the purse spans all three answers either way.
        """
        minimum_loot, maximum_loot = self.get_min_max_loot()

        return self._priced_for_expected_opposition(full_band_loot=round((minimum_loot + maximum_loot) / 2))
