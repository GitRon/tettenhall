from django.db import models
from django.db.models import QuerySet

from apps.warband.faction.managers.faction import FactionManager
from apps.warband.faction.models.culture import Culture
from apps.warband.item.models import Item
from apps.warband.quest.models import Quest
from apps.warband.skirmish.models import Warrior


class Faction(models.Model):
    name = models.CharField("Name", max_length=100)
    culture = models.ForeignKey(Culture, verbose_name="Culture", on_delete=models.CASCADE)
    fyrd_reserve = models.PositiveSmallIntegerField(
        "Fyrd reserve", default=0, help_text="Number of warriors draft-able from the fyrd"
    )
    active_quests = models.ManyToManyField(
        "warband.QuestContract",
        verbose_name="Active Quest",
        blank=True,
        help_text="There can only be one active quest at a time.",
    )
    leader = models.ForeignKey(
        "warband.Warrior",
        verbose_name="Leader",
        related_name="leading_factions",
        on_delete=models.CASCADE,
        null=True,
        blank=False,
    )

    captured_warriors = models.ManyToManyField(
        "warband.Warrior",
        verbose_name="Captured warriors",
        blank=True,
    )
    # Set when the leader is killed or captured. The faction row stays: "leader" is the only remaining
    # record of who led it once capture has cleared the warrior's own faction
    is_defeated = models.BooleanField("Is defeated", default=False)
    savegame = models.ForeignKey("warband.Savegame", verbose_name="Savegame", on_delete=models.CASCADE)

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

    @property
    def renown(self) -> int:
        """
        What the faction is known for, which is what its leader is known for.

        Read through the leader rather than stored, so it cannot drift from him. A defeated faction is
        known for nothing: "leader" still points at the man it lost, dead or in somebody else's cell,
        and his name is no longer the faction's.
        """
        if self.is_defeated or self.leader is None:
            return 0

        return self.leader.renown

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
        Whether this faction's war band has already taken the field this month.

        A war band marches once a month, and it is out whenever its leader went into a fight - every
        attack, and a quest when he was sent on it. Asked of the fights rather than of the man leading
        today: a leader who falls is succeeded mid-month, and the man who takes the seat may have stayed
        at home and be busy with nothing. A quest fought without the leader leaves the march open, as it
        leaves the leader free.
        """
        return self.attacking_skirmishes.filter(month=month, attacking_leader__isnull=False).exists()

    def can_march_this_month(self, *, month: int) -> bool:
        """
        Whether this faction may put a war band in the field this month.

        Two conditions, and both are needed: the month's march not yet spent, and a leader fit and free
        to lead the next one. The first is not implied by the second once a fallen leader's successor
        sits in his place, and the second is not implied by the first while the leader lies wounded.
        """
        return not self.has_marched_this_month(month=month) and self.get_available_leader(month=month) is not None

    def get_monthly_income(self) -> int:
        """
        What this faction's town pays out when a month turns, for the men it keeps today.

        The one head-count behind the figure, because the month pays it and the cost card promises it a
        page earlier, and the two have to get the same answer. Counted every time rather than stored: a
        player who hires in month twelve is paid the fuller revenue in month twelve, and one whose war
        band walks out is back to the baseline the month after.
        """
        warriors_on_payroll = Warrior.objects.filter_drawing_a_wage().filter_faction(faction_id=self.id).count()

        return self.town.get_monthly_income(warriors_on_payroll=warriors_on_payroll)

    def get_all_unoccupied_items(self) -> QuerySet:
        from apps.warband.item.models.item import Item

        return Item.objects.filter(owner=self, warrior_weapon__isnull=True, warrior_armor__isnull=True)

    def get_all_living_warriors(self) -> QuerySet:
        """
        The men this faction can still be asked to do something with.

        The gear they hold comes along, because the one caller - the "Give to" picker on an unused
        item - names what each man has in the slot before the player displaces it. Reading that off
        the card instead would be one query per option.
        """
        return (
            Warrior.objects.exclude_dead()
            .filter_faction(faction_id=self.id)
            .select_related("weapon__type", "armor__type")
        )

    def get_held_captives(self) -> QuerySet:
        """
        The prisoners in this faction's cells, as the captive list renders them.

        Read through here rather than as "captured_warriors.all" in the template, for the reason
        [get_all_living_warriors] exists: the row names the weapon and the armour a man carries, an
        item's name reads its type, and a bare related manager makes that up to four queries per
        prisoner.
        """
        return self.captured_warriors.select_related("weapon__type", "armor__type").with_portrait()

    def get_pub_stock(self) -> QuerySet:
        """
        The men standing in this faction's pub, with the gear the row names along for it, and the
        savegame his price reads the current month off - see [Warrior.months_in_pub].

        The twin of [get_held_captives], and separate because they are two different relations - the
        pub is what a faction is offering and the cells are what it is holding.
        """
        return self.available_mercenaries.select_related("weapon__type", "armor__type", "savegame").with_portrait()
