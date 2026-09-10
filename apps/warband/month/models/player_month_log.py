from typing import ClassVar

from django.db import models

from apps.warband.faction.models import Faction
from apps.warband.month.managers.player_month_log import PlayerMonthLogManager


class PlayerMonthLog(models.Model):
    class CategoryChoices(models.IntegerChoices):
        CATEGORY_ATTENTION = 1, "Demands attention"
        CATEGORY_CONSEQUENCE = 2, "Consequence"
        CATEGORY_UPKEEP = 3, "Upkeep"
        CATEGORY_CHRONICLE = 4, "Chronicle"

    class KindChoices(models.IntegerChoices):
        KIND_UNPAID_SALARIES = 1, "Salaries unpaid"
        KIND_WARRIOR_WALKED_OUT = 2, "Warrior walked out"
        KIND_SALARIES_PAID = 3, "Salaries paid"
        KIND_BUILDING_INCOME = 4, "Building income"
        KIND_FYRD_GROWTH = 5, "Fyrd growth"
        KIND_SKILL_UPGRADE = 6, "Skill upgrade"
        KIND_MORALE_RECOVERED = 7, "Morale recovered"
        KIND_WOUNDS_HEALED = 8, "Wounds healed"
        KIND_QUESTS_OFFERED = 9, "Quests offered"
        KIND_PUB_RESTOCKED = 10, "Pub restocked"
        KIND_SHOP_RESTOCKED = 11, "Shop restocked"
        # One kind for every incident rather than one per incident: adding an entry to the catalogue
        # has to cost a single class, and a kind of its own would touch this model, its choices and
        # KIND_CATEGORIES every time
        KIND_INCIDENT = 12, "Incident"
        KIND_WARRIOR_DISMISSED = 13, "Warrior dismissed"
        KIND_MORALE_LOST_UNPAID = 14, "Morale lost over unpaid wages"
        KIND_SAVEGAME_ENDED = 15, "Savegame ended"

    # How loudly a kind is allowed to speak. Derived rather than passed alongside the kind, so a
    # producer names one thing and the two can never disagree about the same line.
    KIND_CATEGORIES: ClassVar[dict[int, int]] = {
        KindChoices.KIND_UNPAID_SALARIES: CategoryChoices.CATEGORY_ATTENTION,
        KindChoices.KIND_WARRIOR_WALKED_OUT: CategoryChoices.CATEGORY_ATTENTION,
        KindChoices.KIND_SALARIES_PAID: CategoryChoices.CATEGORY_CONSEQUENCE,
        KindChoices.KIND_BUILDING_INCOME: CategoryChoices.CATEGORY_CONSEQUENCE,
        KindChoices.KIND_FYRD_GROWTH: CategoryChoices.CATEGORY_CONSEQUENCE,
        KindChoices.KIND_SKILL_UPGRADE: CategoryChoices.CATEGORY_CONSEQUENCE,
        KindChoices.KIND_MORALE_RECOVERED: CategoryChoices.CATEGORY_UPKEEP,
        KindChoices.KIND_WOUNDS_HEALED: CategoryChoices.CATEGORY_UPKEEP,
        KindChoices.KIND_QUESTS_OFFERED: CategoryChoices.CATEGORY_CONSEQUENCE,
        KindChoices.KIND_PUB_RESTOCKED: CategoryChoices.CATEGORY_CONSEQUENCE,
        KindChoices.KIND_SHOP_RESTOCKED: CategoryChoices.CATEGORY_CONSEQUENCE,
        KindChoices.KIND_INCIDENT: CategoryChoices.CATEGORY_CHRONICLE,
        # A consequence and not something demanding attention, unlike a man walking out: the player
        # decided this one, so the line records what he did rather than warning him it happened to him
        KindChoices.KIND_WARRIOR_DISMISSED: CategoryChoices.CATEGORY_CONSEQUENCE,
        # Upkeep and not attention, even though morale is what routs a man mid-fight: the shortfall
        # line is the one asking to be acted on, and a second loud line about the same month's wages
        # would compete with it. This one is the count of who took it to heart
        KindChoices.KIND_MORALE_LOST_UNPAID: CategoryChoices.CATEGORY_UPKEEP,
        # A chronicle entry, like an incident: it is the one thing in the log that happened to the
        # player rather than something he did, and the only other kind with a second sentence to say
        KindChoices.KIND_SAVEGAME_ENDED: CategoryChoices.CATEGORY_CHRONICLE,
    }

    # Upkeep is reported as one tallied sentence per kind rather than one line per warrior, so each
    # upkeep kind needs a phrase to be counted into. Singular and plural, the way the log's own
    # producers word their counts. Every upkeep kind needs an entry - a missing one is a KeyError
    # rather than a silent fallback, and a test holds the two dicts to the same set of kinds.
    UPKEEP_SUMMARY_PHRASES: ClassVar[dict[int, tuple[str, str]]] = {
        KindChoices.KIND_MORALE_RECOVERED: ("warrior recovered his morale", "warriors recovered their morale"),
        KindChoices.KIND_WOUNDS_HEALED: ("warrior was healed", "warriors were healed"),
        KindChoices.KIND_MORALE_LOST_UNPAID: (
            "warrior lost heart over unpaid wages",
            "warriors lost heart over unpaid wages",
        ),
    }

    title = models.CharField("Title", max_length=100)
    # The room a chronicle entry needs and no other kind has: a report sentence fits in the title,
    # the sentence that undercuts it does not. Empty for every other producer, so the log stays one
    # line wherever it always was
    body = models.TextField("Body", blank=True, default="")
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
