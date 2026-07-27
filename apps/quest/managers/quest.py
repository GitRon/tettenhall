from django.db import models
from django.db.models import manager


class QuestQuerySet(models.QuerySet):
    def for_savegame(self, *, savegame_id: int):
        # A quest belongs to a savegame through the faction it targets
        return self.filter(target_faction__savegame_id=savegame_id)

    def for_player_faction(self, *, faction_id: int):
        # Only what is pinned to that faction's bulletin board: a quest of the right savegame can
        # still be one that was never offered to the player
        return self.filter(available_town_quests=faction_id)


class QuestManager(manager.Manager):
    pass


QuestManager = QuestManager.from_queryset(QuestQuerySet)
