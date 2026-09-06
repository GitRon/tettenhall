from typing import ClassVar

from django.db import models

from apps.faction.models import Faction
from apps.month.managers.player_month_log import PlayerMonthLogManager


class PlayerMonthLog(models.Model):
    class CategoryChoices(models.IntegerChoices):
        CATEGORY_ATTENTION = 1, "Demands attention"
        CATEGORY_CONSEQUENCE = 2, "Consequence"
        CATEGORY_UPKEEP = 3, "Upkeep"

    class KindChoices(models.IntegerChoices):
        KIND_UNPAID_SALARIES = 1, "Salaries unpaid"
        KIND_WARRIOR_DESERTED = 2, "Warrior deserted"
        KIND_SALARIES_PAID = 3, "Salaries paid"
        KIND_BUILDING_INCOME = 4, "Building income"
        KIND_FYRD_GROWTH = 5, "Fyrd growth"
        KIND_SKILL_UPGRADE = 6, "Skill upgrade"
        KIND_MORALE_RECOVERED = 7, "Morale recovered"
        KIND_WOUNDS_HEALED = 8, "Wounds healed"

    # How loudly a kind is allowed to speak. Derived rather than passed alongside the kind, so a
    # producer names one thing and the two can never disagree about the same line.
    KIND_CATEGORIES: ClassVar[dict[int, int]] = {
        KindChoices.KIND_UNPAID_SALARIES: CategoryChoices.CATEGORY_ATTENTION,
        KindChoices.KIND_WARRIOR_DESERTED: CategoryChoices.CATEGORY_ATTENTION,
        KindChoices.KIND_SALARIES_PAID: CategoryChoices.CATEGORY_CONSEQUENCE,
        KindChoices.KIND_BUILDING_INCOME: CategoryChoices.CATEGORY_CONSEQUENCE,
        KindChoices.KIND_FYRD_GROWTH: CategoryChoices.CATEGORY_CONSEQUENCE,
        KindChoices.KIND_SKILL_UPGRADE: CategoryChoices.CATEGORY_CONSEQUENCE,
        KindChoices.KIND_MORALE_RECOVERED: CategoryChoices.CATEGORY_UPKEEP,
        KindChoices.KIND_WOUNDS_HEALED: CategoryChoices.CATEGORY_UPKEEP,
    }

    # Upkeep is reported as one tallied sentence per kind rather than one line per warrior, so each
    # upkeep kind needs a phrase to be counted into. Singular and plural, the way the log's own
    # producers word their counts. Every upkeep kind needs an entry - a missing one is a KeyError
    # rather than a silent fallback, and a test holds the two dicts to the same set of kinds.
    UPKEEP_SUMMARY_PHRASES: ClassVar[dict[int, tuple[str, str]]] = {
        KindChoices.KIND_MORALE_RECOVERED: ("warrior recovered his morale", "warriors recovered their morale"),
        KindChoices.KIND_WOUNDS_HEALED: ("warrior was healed", "warriors were healed"),
    }

    title = models.CharField("Title", max_length=100)
    kind = models.PositiveSmallIntegerField("Kind", choices=KindChoices.choices)
    category = models.PositiveSmallIntegerField("Category", choices=CategoryChoices.choices)
    month = models.PositiveSmallIntegerField("Month")
    faction = models.ForeignKey(Faction, verbose_name="Faction", on_delete=models.CASCADE)

    objects = PlayerMonthLogManager()

    class Meta:
        verbose_name = "Player month log"
        verbose_name_plural = "Player month logs"
        default_related_name = "player_month_logs"
        # Newest month first, and within a month the order the lines were written, so the list reads
        # the way the month happened rather than in whatever order the database hands the rows back
        ordering = ("-month", "id")

    def __str__(self) -> str:
        return self.title
