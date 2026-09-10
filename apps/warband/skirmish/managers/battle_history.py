from django.db import models
from django.db.models import manager


class BattleHistoryQuerySet(models.QuerySet):
    def for_savegame(self, *, savegame_id: int):
        return self.filter(skirmish__attacking_faction__savegame_id=savegame_id)


class BattleHistoryManager(manager.Manager):
    def create_record(self, *, skirmish, message, kind, warrior=None):
        """
        Writes one line of a fight.

        Takes the warrior a line is about and files the side he fought for itself, rather than letting
        the producer hand in both: which faction a man belongs to is his to answer, and a line naming
        one warrior and another man's faction would be a row nothing could notice was wrong.
        """
        return self.create(
            skirmish=skirmish,
            message=message,
            kind=kind,
            faction_id=warrior.faction_id if warrior else None,
        )


BattleHistoryManager = BattleHistoryManager.from_queryset(BattleHistoryQuerySet)
