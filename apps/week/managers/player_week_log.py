from django.db import models
from django.db.models import manager


class PlayerWeekLogQuerySet(models.QuerySet):
    pass


class PlayerWeekLogManager(manager.Manager):
    def create_record(self, *, title: str, message: str, week: int):
        return self.create(
            title=title,
            message=message,
            week=week,
        )


PlayerWeekLogManager = PlayerWeekLogManager.from_queryset(PlayerWeekLogQuerySet)
