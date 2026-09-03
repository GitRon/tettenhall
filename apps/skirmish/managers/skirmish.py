from django.db import models
from django.db.models import manager


class SkirmishQuerySet(models.QuerySet):
    def for_savegame(self, *, savegame_id: int):
        return self.filter(attacking_faction__savegame_id=savegame_id)

    def unresolved(self):
        return self.filter(victorious_faction__isnull=True)

    def has_started(self):
        return self.filter(current_round__gt=1)


class SkirmishManager(manager.Manager):
    def increment_round(self, *, skirmish):
        skirmish.refresh_from_db()
        skirmish.current_round += 1
        return skirmish.save()

    def set_victor(self, *, skirmish, victorious_faction) -> bool:
        """
        Writes the victor onto a skirmish that has none, and answers whether it was this call.

        A single conditional UPDATE rather than a read-modify-save, because two passes can reach the
        same fight: killing the player's leader ends the savegame, which force-resolves every open
        skirmish - including the one that round is still resolving. The two passes hold separate
        instances of the same row, so nothing in memory can see the other's write. Refusing the
        second here is what keeps the loser from being stripped twice and the quest from paying
        twice.
        """
        updated = self.filter(pk=skirmish.pk, victorious_faction__isnull=True).update(
            victorious_faction=victorious_faction
        )
        if not updated:
            return False

        skirmish.victorious_faction = victorious_faction
        return True


SkirmishManager = SkirmishManager.from_queryset(SkirmishQuerySet)
