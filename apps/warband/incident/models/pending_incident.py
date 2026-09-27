from django.db import models

from apps.warband.faction.models.faction import Faction
from apps.warband.incident.managers.pending_incident import PendingIncidentManager
from apps.warband.item.models.item import Item


class PendingIncident(models.Model):
    """
    A question the world has put to the player and he has not answered yet.

    Not a month log line: "PlayerMonthLog" is cleared at every month advance, and a question has to
    survive until it is answered - by the player, or by its default when the month he was asked in
    ends. So it lives one month at most, and the answer is what reaches the log.

    "incident" names the entry's class in the pool, which is where the options and what each one
    does are declared. "rival" and "item" are what the question was about, kept so the answer lands
    on the same rival and the same piece of gear.
    """

    faction = models.ForeignKey(Faction, verbose_name="Faction", on_delete=models.CASCADE)
    month = models.PositiveSmallIntegerField("Month")
    incident = models.CharField("Incident", max_length=50)
    title = models.CharField("Title", max_length=100)
    body = models.TextField("Body", blank=True, default="")
    rival = models.ForeignKey(
        Faction,
        verbose_name="Rival",
        on_delete=models.CASCADE,
        related_name="pending_incidents_as_rival",
        null=True,
        blank=True,
    )
    # Nulled rather than cascaded: the gear can be lost or sold while the question waits, and the
    # question then still has its default answer to give
    item = models.ForeignKey(
        Item,
        verbose_name="Item",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    objects = PendingIncidentManager()

    class Meta:
        verbose_name = "Pending incident"
        verbose_name_plural = "Pending incidents"
        default_related_name = "pending_incidents"
        ordering = ("id",)

    def __str__(self) -> str:
        return self.title
