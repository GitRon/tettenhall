from django.db import models
from django.db.models import manager


class SkirmishSpoilQuerySet(models.QuerySet):
    def for_skirmish(self, *, skirmish_id: int):
        return self.filter(skirmish_id=skirmish_id)


class SkirmishSpoilManager(manager.Manager):
    def create_record(self, *, skirmish, faction, kind, item=None, warrior=None, amount=0, description=""):
        return self.create(
            skirmish=skirmish,
            faction=faction,
            kind=kind,
            item=item,
            warrior=warrior,
            amount=amount,
            description=description,
        )


SkirmishSpoilManager = SkirmishSpoilManager.from_queryset(SkirmishSpoilQuerySet)
