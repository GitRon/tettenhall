from django.db import models

from apps.warband.skirmish.models.skirmish import Skirmish
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.warrior.choices.nickname import NicknameStateChoices
from apps.warband.warrior.choices.warrior_milestone import JoinedWayChoices, MilestoneKindChoices
from apps.warband.warrior.managers.warrior_milestone import WarriorMilestoneManager


class WarriorMilestone(models.Model):
    """
    One moment in a man's life that nothing else in the game keeps: how he came onto a roster, the seat
    he took, the epithet he earned and why, the fight that made something of him.

    Written as it happens rather than reconstructed, because each of these leaves nothing behind on him
    but a column that the next moment overwrites - a nickname state, a faction. Never edited once
    written, so it goes in through "create_record" - see docs/patterns/app-layout.md.

    Not called a chronicle: that word already belongs to the month log, which forgets.
    """

    warrior = models.ForeignKey(Warrior, verbose_name="Warrior", on_delete=models.CASCADE)
    kind = models.PositiveSmallIntegerField("Kind", choices=MilestoneKindChoices.choices)
    month = models.PositiveSmallIntegerField("Month")
    # The war band he stood in when it happened - or, for a prisoner, the one holding him - stamped here
    # because he may serve another by the time anybody reads it. Whether the player saw it happen is read
    # off this
    faction = models.ForeignKey(
        "warband.Faction",
        verbose_name="Faction",
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    # The fight it happened in, for the moments a fight brings. Kept when the fight's row goes, because
    # the moment happened either way
    skirmish = models.ForeignKey(
        Skirmish,
        verbose_name="Skirmish",
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    # The other war band in it: the one that seized him in his occupied town
    other_faction = models.ForeignKey(
        "warband.Faction",
        verbose_name="Other faction",
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    # The other man in it: the one he felled for his epithet, or the leader whose seat he took
    other_warrior = models.ForeignKey(
        Warrior,
        verbose_name="Other warrior",
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    # The epithet he earned, as the state rather than the wording - his own "nickname_variant" phrases
    # it, the way it phrases the one on his card
    nickname_state = models.PositiveSmallIntegerField(
        "Nickname state", choices=NicknameStateChoices.choices, null=True, blank=True
    )
    joined_way = models.PositiveSmallIntegerField("Joined by", choices=JoinedWayChoices.choices, null=True, blank=True)

    objects = WarriorMilestoneManager()

    class Meta:
        verbose_name = "Warrior milestone"
        verbose_name_plural = "Warrior milestones"
        default_related_name = "milestones"
        # The order they happened in
        ordering = ("id",)

    def __str__(self) -> str:
        return f"{self.warrior}: {self.get_kind_display()}"
