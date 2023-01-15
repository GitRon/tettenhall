from django.db import models
from django.db.models import manager


class SkirmishQuerySet(models.QuerySet):
    pass


class SkirmishManager(manager.Manager):
    def increment_round(self, skirmish):
        skirmish.current_round += 1
        return skirmish.save()

    def set_victor(self, skirmish, victorious_faction):
        skirmish.victorious_faction = victorious_faction
        return skirmish.save()


SkirmishManager = SkirmishManager.from_queryset(SkirmishQuerySet)
