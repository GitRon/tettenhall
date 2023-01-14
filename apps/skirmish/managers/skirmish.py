from django.db import models
from django.db.models import manager


class SkirmishQuestSet(models.QuerySet):
    pass


class SkirmishManager(manager.Manager):
    def increment_round(self, skirmish):
        skirmish.current_round += 1
        return skirmish.save()


SkirmishManager = SkirmishManager.from_queryset(SkirmishQuestSet)
