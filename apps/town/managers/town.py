from django.db import models
from django.db.models import manager


class TownQuerySet(models.QuerySet):
    def for_savegame(self, *, savegame_id: int):
        return self.filter(faction__savegame=savegame_id)


class TownManager(manager.Manager):
    pass


TownManager = TownManager.from_queryset(TownQuerySet)
