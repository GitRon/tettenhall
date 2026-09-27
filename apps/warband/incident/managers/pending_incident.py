from django.db import models


class PendingIncidentQuerySet(models.QuerySet):
    def for_savegame(self, *, savegame_id: int):
        return self.filter(faction__savegame=savegame_id)

    def for_player_faction(self, *, faction_id: int):
        # A question is put to the player's own faction, so the id from the URL must not reach one
        # the savegame holds for anybody else
        return self.filter(faction_id=faction_id)

    def asked_before(self, *, month: int):
        return self.filter(month__lt=month)


PendingIncidentManager = models.Manager.from_queryset(PendingIncidentQuerySet)
