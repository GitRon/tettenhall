from django.db import models
from django.db.models import manager


class QuestQuerySet(models.QuerySet):
    def for_player_faction(self, *, faction_id: int):
        return self.filter(faction_id=faction_id)

    def offered_in(self, *, month: int):
        return self.filter(month=month)


class QuestManager(manager.Manager):
    pass


QuestManager = QuestManager.from_queryset(QuestQuerySet)
