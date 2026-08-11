from django.db import models
from django.db.models import manager


class FactionQuerySet(models.QuerySet):
    def for_savegame(self, *, savegame_id: int):
        return self.filter(savegame=savegame_id)

    def for_player_faction(self, *, faction_id: int):
        return self.filter(id=faction_id)

    def rivals_of(self, *, savegame_id: int, player_faction_id: int | None):
        """
        Every faction of the savegame the player does not control.

        A savegame without a player faction yet is a reachable state, and excluding "None" keeps
        every row rather than dropping them - there is nobody to exclude at that point.

        This is the one place deciding which rivals still take part in the game, so the "is this
        faction defeated" filter belongs here once that flag exists.
        """
        return self.for_savegame(savegame_id=savegame_id).exclude(id=player_faction_id)


class FactionManager(manager.Manager):
    def add_captive(self, *, faction, warrior):
        faction.captured_warriors.add(warrior)

    def remove_captive(self, *, faction, warrior):
        faction.captured_warriors.remove(warrior)

    def replenish_fyrd_reserve(self, *, faction, new_recruitees: int):
        faction.refresh_from_db()

        # Update reserve
        faction.fyrd_reserve += new_recruitees
        faction.save()

        return faction

    def reduce_fyrd_reserve(self, *, faction, drafted_warriors: int):
        faction.refresh_from_db()

        # Update reserve
        faction.fyrd_reserve = max(0, faction.fyrd_reserve - drafted_warriors)
        faction.save()

        return faction


FactionManager = FactionManager.from_queryset(FactionQuerySet)
