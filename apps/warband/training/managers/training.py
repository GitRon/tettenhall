from django.db import models
from django.db.models import manager


class TrainingQuerySet(models.QuerySet):
    def filter_faction(self, *, faction_id: int):
        # The regimen this faction trains by. Parameterised rather than player-scoped: every faction
        # of the savegame owns a row and trains by it, and the caller passing a faction is what says
        # whose month is being worked
        return self.filter(faction_id=faction_id)

    def for_player_faction(self, *, faction_id: int):
        # Every faction of a savegame owns a training row, so scoping to the savegame is not enough
        # to single out the player's own
        return self.filter(faction_id=faction_id)


class TrainingManager(manager.Manager):
    pass


TrainingManager = TrainingManager.from_queryset(TrainingQuerySet)
