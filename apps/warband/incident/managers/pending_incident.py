from django.db import models


class PendingIncidentQuerySet(models.QuerySet):
    def for_player_faction(self, *, faction_id: int):
        # A question is put to the player's own faction, so the id from the URL must not reach one
        # the savegame holds for anybody else
        return self.filter(faction_id=faction_id)

    def asked_before(self, *, month: int):
        return self.filter(month__lt=month)

    def close(self, *, pending_incident) -> bool:
        """
        Take a question off the table, and say whether it was still on it.

        A filtered delete rather than "pending_incident.delete()", which raises nothing when the row is
        already gone: two overlapping answers both find the question open, and the one whose delete
        comes back empty is the one that must not land a second time.
        """
        deleted_rows, _ = self.filter(id=pending_incident.id).delete()

        return deleted_rows > 0


PendingIncidentManager = models.Manager.from_queryset(PendingIncidentQuerySet)
