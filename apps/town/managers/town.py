from django.db import models
from django.db.models import manager


class TownQuerySet(models.QuerySet):
    def for_player_faction(self, *, faction_id: int):
        # Scoping to the savegame would still cover the rival towns, and the town views act on the
        # one the player owns
        return self.filter(faction_id=faction_id)


class TownManager(manager.Manager):
    pass


TownManager = TownManager.from_queryset(TownQuerySet)
