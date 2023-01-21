from django.db import models
from django.db.models import manager


class FactionQuerySet(models.QuerySet):
    pass


class FactionManager(manager.Manager):
    def add_captive(self, faction, warrior):
        faction.captured_warriors.add(warrior)
        return faction.save()


FactionManager = FactionManager.from_queryset(FactionQuerySet)
