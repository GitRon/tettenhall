from django.db import models
from django.db.models import manager


class WarriorQuestSet(models.QuerySet):
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


WarriorManager = WarriorManager.from_queryset(WarriorQuestSet)
