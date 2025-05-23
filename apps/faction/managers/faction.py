from django.db import models
from django.db.models import manager


class FactionQuerySet(models.QuerySet):
    def for_savegame(self, *, savegame_id: int):
        return self.filter(savegame=savegame_id)


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
