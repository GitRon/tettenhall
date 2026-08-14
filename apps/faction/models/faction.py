from django.db import models
from django.db.models import QuerySet

from apps.faction.managers.faction import FactionManager
from apps.faction.models.culture import Culture
from apps.item.models import Item
from apps.quest.models import Quest
from apps.skirmish.models import Warrior


class Faction(models.Model):
    name = models.CharField("Name", max_length=100)
    culture = models.ForeignKey(Culture, verbose_name="Culture", on_delete=models.CASCADE)
    fyrd_reserve = models.PositiveSmallIntegerField(
        "Fyrd reserve", default=0, help_text="Number of warriors draft-able from the fyrd"
    )
    active_quests = models.ManyToManyField(
        "quest.QuestContract",
        verbose_name="Active Quest",
        blank=True,
        help_text="There can only be one active quest at a time.",
    )
    leader = models.ForeignKey(
        "skirmish.Warrior",
        verbose_name="Leader",
        related_name="leading_factions",
        on_delete=models.CASCADE,
        null=True,
        blank=False,
    )

    captured_warriors = models.ManyToManyField(
        "skirmish.Warrior",
        verbose_name="Captured warriors",
        blank=True,
    )
    # Set when the leader is killed or captured. The faction row stays: "leader" is the only remaining
    # record of who led it once capture has cleared the warrior's own faction
    is_defeated = models.BooleanField("Is defeated", default=False)
    savegame = models.ForeignKey("savegame.Savegame", verbose_name="Savegame", on_delete=models.CASCADE)

    town_name = models.CharField("Town name", max_length=100)
    available_items = models.ManyToManyField(
        Item, verbose_name="Available items", related_name="available_shop_items", blank=True
    )
    available_mercenaries = models.ManyToManyField(
        Warrior, verbose_name="Available mercenaries", related_name="available_pub_mercenaries", blank=True
    )
    available_quests = models.ManyToManyField(
        Quest, verbose_name="Available quests", related_name="available_town_quests", blank=True
    )

    objects = FactionManager()

    class Meta:
        verbose_name = "Faction"
        verbose_name_plural = "Factions"
        default_related_name = "factions"

    def __str__(self) -> str:
        return self.name

    def get_available_leader(self, *, month: int) -> Warrior | None:
        """
        The faction's leader, if he is fit to march this month.

        "The leader always joins" is the one part of a war band the player does not get to compose,
        so a leader who is wounded, dead or already promised to a quest is not a warrior to leave at
        home - it means the faction has no attack to launch at all.
        """
        if self.leader_id is None:
            return None

        return Warrior.objects.filter_healthy().filter(id=self.leader_id).exclude_currently_busy(month=month).first()

    def has_marched_this_month(self, *, month: int) -> bool:
        """
        Whether this faction's war band has already been committed to a fight this month.

        Asked of the leader, because he is the one who joins every attack - once he is busy, nothing
        the faction does can put another war band in the field. Only here to tell the player why the
        attack button is gone; the guarding is done by [get_available_leader].
        """
        if self.leader_id is None:
            return False

        return not Warrior.objects.filter(id=self.leader_id).exclude_currently_busy(month=month).exists()

    def get_all_unoccupied_items(self) -> QuerySet:
        from apps.item.models.item import Item

        return Item.objects.filter(owner=self, warrior_weapon__isnull=True, warrior_armor__isnull=True)
