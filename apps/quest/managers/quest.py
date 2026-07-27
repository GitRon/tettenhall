from django.db import models
from django.db.models import manager


class QuestQuerySet(models.QuerySet):
    def for_savegame(self, *, savegame_id: int):
        # A quest belongs to a savegame through the faction it targets
        return self.filter(target_faction__savegame_id=savegame_id)


class QuestManager(manager.Manager):
    pass


QuestManager = QuestManager.from_queryset(QuestQuerySet)
