from django.db import models
from django.db.models import manager


class PlayerWeekLogQuerySet(models.QuerySet):
    def for_user(self, *, user_id: int):
        return self.filter(savegame__created_by=user_id)


class PlayerWeekLogManager(manager.Manager):
    def create_record(self, *, title: str, message: str, week: int, faction_id: int):
        return self.create(
            title=title,
            message=message,
            week=week,
            faction_id=faction_id,
        )


PlayerWeekLogManager = PlayerWeekLogManager.from_queryset(PlayerWeekLogQuerySet)
