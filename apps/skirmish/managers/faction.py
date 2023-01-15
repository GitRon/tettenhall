from django.db import models
from django.db.models import manager


class FactionQuerySet(models.QuerySet):
    pass


class FactionManager(manager.Manager):
    def aquire_loot(self, faction, item):
        faction.stored_items.add(item)
        return faction.save()


FactionManager = FactionManager.from_queryset(FactionQuerySet)
