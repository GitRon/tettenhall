from django.db import models
from django.db.models import manager


class BattleHistoryQuerySet(models.QuerySet):
    pass


class BattleHistoryManager(manager.Manager):
    def create_record(self, skirmish, message):
        return self.create(
            skirmish=skirmish,
            message=message,
        )


WarriorManager = BattleHistoryManager.from_queryset(BattleHistoryQuerySet)
