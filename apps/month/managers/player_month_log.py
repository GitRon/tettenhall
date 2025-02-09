from django.db import models
from django.db.models import manager


class PlayerMonthLogQuerySet(models.QuerySet):
    def for_savegame(self, *, savegame_id: int):
        return self.filter(faction__savegame=savegame_id)


class PlayerMonthLogManager(manager.Manager):
    def create_record(self, *, title: str, month: int, faction_id: int):
        return self.create(
            title=title,
            month=month,
            faction_id=faction_id,
        )


PlayerMonthLogManager = PlayerMonthLogManager.from_queryset(PlayerMonthLogQuerySet)
