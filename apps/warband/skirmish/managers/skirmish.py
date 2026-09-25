from django.db import models
from django.db.models import manager


class SkirmishQuerySet(models.QuerySet):
    def for_savegame(self, *, savegame_id: int):
        return self.filter(attacking_faction__savegame_id=savegame_id)

    def unresolved(self):
        return self.filter(victorious_faction__isnull=True)

    def resolved(self):
        return self.filter(victorious_faction__isnull=False)

    def has_started(self):
        return self.filter(current_round__gt=1)


class SkirmishManager(manager.Manager):
    def increment_round(self, *, skirmish):
        skirmish.refresh_from_db()
        skirmish.current_round += 1
        return skirmish.save()

    def batter_fortification(self, *, skirmish, damage: int) -> int:
        """
        Takes a blow off the wall and answers how much of it the wall actually lost.

        Never below zero: a wall that has fallen has nothing more to give, so a second man storming it
        in the same round takes nothing off it. Written to the instance the round is carrying as well as
        to the row, because every blow still to be struck this round reads the wall off that instance.
        """
        skirmish.refresh_from_db(fields=("fortification_strength",))
        lost = min(damage, skirmish.fortification_strength)
        skirmish.fortification_strength -= lost
        skirmish.save(update_fields=("fortification_strength",))
        return lost

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
