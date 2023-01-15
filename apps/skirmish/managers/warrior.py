from django.db import models
from django.db.models import manager


class WarriorQuerySet(models.QuerySet):
    pass


class WarriorManager(manager.Manager):
    def reduce_current_health(self, obj, damage: int):
        obj.current_health -= damage
        obj.save()

        return obj

    def set_condition(self, obj, condition: int):
        obj.condition = condition
        obj.save()

        return obj

    def take_item_away(self, item):
        """
        Ensure that the given "item" is not being actively used by any warrior
        """
        self.filter(weapon=item).update(weapon=None)
        self.filter(armor=item).update(armor=None)


WarriorManager = WarriorManager.from_queryset(WarriorQuerySet)
