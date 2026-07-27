from django.db import models
from django.db.models import manager


class TrainingQuerySet(models.QuerySet):
    def for_savegame(self, *, savegame_id: int):
        return self.filter(faction__savegame=savegame_id)

    def for_player_faction(self, *, faction_id: int):
        # Every faction of a savegame owns a training row, so scoping to the savegame is not enough
        # to single out the player's own
        return self.filter(faction_id=faction_id)


class TrainingManager(manager.Manager):
    pass


TrainingManager = TrainingManager.from_queryset(TrainingQuerySet)
