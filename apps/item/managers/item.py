from django.db import models
from django.db.models import manager


class ItemQuerySet(models.QuerySet):
    pass


class ItemManager(manager.Manager):
    def update_ownership(self, item, new_owner):
        item.owner = new_owner
        return item.save()


ItemManager = ItemManager.from_queryset(ItemQuerySet)
