from typing import ClassVar

from django.db import models

from apps.warband.skirmish.managers.battle_history import BattleHistoryManager
from apps.warband.skirmish.models.skirmish import Skirmish


class BattleHistory(models.Model):
    class KindChoices(models.IntegerChoices):
        # One kind for the whole blow-by-blow rather than one per producer. Fifteen handlers write
        # these lines and the panel only has to pick out the ones where a man went down - telling a
        # missed swing from a round closing would be a distinction nothing reads.
        KIND_NARRATION = 1, "Narration"
        KIND_WARRIOR_KILLED = 2, "Warrior killed"
        KIND_WARRIOR_INCAPACITATED = 3, "Warrior knocked unconscious"
        # Both ways off the field under one kind. The wording splits them because a player who
        # ordered a retreat must not be told his man broke; the marking does not, because what it
        # answers is whether the man is gone.
        KIND_WARRIOR_LEFT_THE_FIELD = 4, "Warrior left the field"

    # The kinds that take a man out of the fight, and the icon each is marked with. Keyed by kind and
    # kept on the model because a Django template cannot compare a value against a choices constant -
    # the same reason PlayerMonthLog keeps its category and phrase tables here. Membership is the
    # whole of what "is_casualty" asks, so the three ways off the field are named once.
    KIND_ICONS: ClassVar[dict[int, str]] = {
        KindChoices.KIND_WARRIOR_KILLED: "fa-skull-crossbones",
        KindChoices.KIND_WARRIOR_INCAPACITATED: "fa-user-injured",
        KindChoices.KIND_WARRIOR_LEFT_THE_FIELD: "fa-person-running",
    }

    message = models.TextField("Message")
    skirmish = models.ForeignKey(Skirmish, verbose_name="Skirmish", on_delete=models.CASCADE)
    kind = models.PositiveSmallIntegerField("Kind", choices=KindChoices.choices, default=KindChoices.KIND_NARRATION)
    # The side the man this line is about fought for, and empty on every line that is about nobody.
    # Kept on the row rather than read back off the warrior, because by the time the panel renders he
    # may belong to the side that beat him: a capture moves him, and the monthly sweep clears the
    # condition that put him here at all.
    faction = models.ForeignKey(
        "warband.Faction", verbose_name="Side he fought for", null=True, blank=True, on_delete=models.CASCADE
    )
    created_at = models.DateTimeField("Created at", auto_now_add=True)

    objects = BattleHistoryManager()

    class Meta:
        verbose_name = "Battle log"
        verbose_name_plural = "Battle logs"
        default_related_name = "battle_logs"
        # The one panel in the game that has to read chronologically, so the order it is written in
        # is part of what it is rather than a detail left to the database
        ordering = ("id",)

    def __str__(self) -> str:
        return self.message

    @property
    def is_casualty(self) -> bool:
        """
        Whether this line reports a man being taken out of the fight, which is what the panel marks.
        """
        return self.kind in self.KIND_ICONS

    @property
    def icon(self) -> str:
        """
        The icon this line is marked with. Only ever asked of a casualty line.
        """
        return self.KIND_ICONS[self.kind]
