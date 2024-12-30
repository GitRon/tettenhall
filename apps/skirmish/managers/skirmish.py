from django.db import models
from django.db.models import manager


class SkirmishQuerySet(models.QuerySet):
    def for_savegame(self, *, savegame_id: int):
        return self.filter(player_faction__savegame_id=savegame_id)

    def unresolved(self):
        return self.filter(victorious_faction__isnull=True)


class SkirmishManager(manager.Manager):
    def increment_round(self, *, skirmish):
        skirmish.refresh_from_db()
        skirmish.current_round += 1
        return skirmish.save()

    def set_victor(self, *, skirmish, victorious_faction):
        skirmish.victorious_faction = victorious_faction
        return skirmish.save()


SkirmishManager = SkirmishManager.from_queryset(SkirmishQuerySet)
