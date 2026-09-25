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
    # Copied off the quest type when the quest is pinned to the board, like the name, so reloading
    # the reference data cannot change the terms of a contract the player has already agreed to
    fortification_strength = models.PositiveSmallIntegerField("Fortification strength", default=0)

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

    def get_fortification_factor(self) -> float:
        """
        What the wall in front of the target adds to the purse, as a factor on it.

        A walled errand is a harder fight for the same men, so without this it would be strictly
        worse than an open one and nobody would pick it twice. Each point of fortification adds
        a hundredth: a settlement errand at 20 pays a fifth more than the same job in open country.
        """
        return 1 + self.fortification_strength / 100

    def _priced(self, *, full_band_loot: int) -> int:
        """
        Turns a full-band figure into what this quest pays.

        Two things decide it beside the difficulty's range, and both are settled when the quest is
        pinned to the board. The target's roster decides the size of the job: a rival who can field
        one man is offering a one-man job at a one-man price. The quest type's wall decides how hard
        that job is. The money follows both here, once, and what the player accepted is then paid in
        full whatever turns out on the day.
        """
        _, band_maximum = self.get_min_max_number_of_opponents()

        return round(full_band_loot * self.expected_opposition / band_maximum * self.get_fortification_factor())

    def calculate_loot(self) -> int:
        minimum_loot, maximum_loot = self.get_min_max_loot()

        return self._priced(full_band_loot=random.randint(minimum_loot, maximum_loot))

    @property
    def average_loot(self) -> int:
        """
        What a quest like this one pays on average, for "obscurify" to describe the purse against.

        Derived from the same range and the same scaling the purse itself came out of, so the word on
        the card stays informative at every roster size and behind every wall instead of reading
        "Low" for every easy quest or "High" for every walled one: a cap of five puts an easy
        quest's thresholds at 200 and 300, a cap of one puts them at 40 and 60, and the purse spans
        all three answers either way.
        """
        minimum_loot, maximum_loot = self.get_min_max_loot()

        return self._priced(full_band_loot=round((minimum_loot + maximum_loot) / 2))
