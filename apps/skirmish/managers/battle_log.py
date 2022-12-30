from django.db import models
from django.db.models import manager


class BattleLogQuestSet(models.QuerySet):
    pass


class BattleLogManager(manager.Manager):
    def create_record(self, skirmish, message):
        return self.create(
            skirmish=skirmish,
            message=message,
        )


WarriorManager = BattleLogManager.from_queryset(BattleLogQuestSet)
