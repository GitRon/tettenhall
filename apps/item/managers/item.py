from django.db import models
from django.db.models import manager


class ItemQuerySet(models.QuerySet):
    pass


class ItemManager(manager.Manager):
    def update_ownership(self, *, item, new_owner):
        from apps.skirmish.models.warrior import Warrior

        # Reset ownership
        item.owner = new_owner
        item.save()

        # Remove from current usages
        Warrior.objects.filter(weapon=item).update(weapon=None)
        Warrior.objects.filter(armor=item).update(armor=None)

        return item


ItemManager = ItemManager.from_queryset(ItemQuerySet)
