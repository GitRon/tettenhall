from django.db import models
from django.db.models import manager


class TrainingQuerySet(models.QuerySet):
    def for_savegame(self, *, savegame_id: int):
        return self.filter(faction__savegame=savegame_id)


class TrainingManager(manager.Manager):
    pass


TrainingManager = TrainingManager.from_queryset(TrainingQuerySet)
