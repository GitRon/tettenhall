from django.db import models
from django.db.models import manager


class BattleHistoryQuerySet(models.QuerySet):
    def for_savegame(self, *, savegame_id: int):
        return self.filter(skirmish__player_faction__savegame_id=savegame_id)


class BattleHistoryManager(manager.Manager):
    def create_record(self, *, skirmish, message):
        return self.create(
            skirmish=skirmish,
            message=message,
        )


BattleHistoryManager = BattleHistoryManager.from_queryset(BattleHistoryQuerySet)
