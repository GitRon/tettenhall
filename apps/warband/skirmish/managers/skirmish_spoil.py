from django.db import models
from django.db.models import manager


class SkirmishSpoilQuerySet(models.QuerySet):
    def for_skirmish(self, *, skirmish_id: int):
        return self.filter(skirmish_id=skirmish_id)


class SkirmishSpoilManager(manager.Manager):
    def create_record(self, *, skirmish, faction, kind, item=None, warrior=None, amount=0):
        return self.create(
            skirmish=skirmish,
            faction=faction,
            kind=kind,
            item=item,
            item_name=item.display_name if item else "",
            item_dice=f"{item.type.base_value}{item.get_modifier_as_string()}" if item else "",
            warrior=warrior,
            amount=amount,
        )


SkirmishSpoilManager = SkirmishSpoilManager.from_queryset(SkirmishSpoilQuerySet)
