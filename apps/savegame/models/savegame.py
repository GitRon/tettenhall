from django.contrib.auth.models import User
from django.db import models

from apps.faction.models import Faction
from apps.marketplace.models import Marketplace
from apps.savegame.managers.savegame import SavegameManager


class Savegame(models.Model):
    name = models.CharField("Name", max_length=75)
    created_by = models.ForeignKey(User, verbose_name="Created by", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    lastmodified_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=False)
    current_month = models.PositiveSmallIntegerField(
        "Current month", default=0, help_text="Month will be incremented after creation via Command"
    )

    player_faction = models.OneToOneField(
        Faction,
        verbose_name="Player Faction",
        on_delete=models.CASCADE,
        related_name="player_savegame",
        null=True,
    )
    marketplace = models.OneToOneField(
        Marketplace,
        verbose_name="Marketplace",
        on_delete=models.CASCADE,
        related_name="savegame",
        null=True,
    )

    objects = SavegameManager()

    class Meta:
        verbose_name = "Savegame"
        verbose_name_plural = "Savegames"
        default_related_name = "savegames"

    def __str__(self) -> str:
        return f"{self.name} ({self.created_by.get_full_name()})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Set all other savegames of this savegames user to inactive
        if self.is_active:
            Savegame.objects.set_all_others_from_user_to_inactive(savegame_id=self.id, user_id=self.created_by.id)
