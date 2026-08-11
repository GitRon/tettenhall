from django.db import models
from django.db.models import manager


class FactionQuerySet(models.QuerySet):
    def for_savegame(self, *, savegame_id: int):
        return self.filter(savegame=savegame_id)

    def for_player_faction(self, *, faction_id: int):
        return self.filter(id=faction_id)

    def still_in_play(self, *, savegame_id: int):
        """
        Every faction of the savegame still taking part in the game, the player's included.

        This is the one place deciding who is still in it, so the "is this faction defeated" filter
        belongs here once that flag exists.
        """
        return self.for_savegame(savegame_id=savegame_id)


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
