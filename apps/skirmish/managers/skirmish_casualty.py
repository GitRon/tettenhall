from django.db import models
from django.db.models import manager


class SkirmishCasualtyQuerySet(models.QuerySet):
    def for_skirmish(self, *, skirmish_id: int):
        return self.filter(skirmish_id=skirmish_id)


class SkirmishCasualtyManager(manager.Manager):
    def record_casualty(self, *, skirmish, warrior, fate: int):
        """
        Stamps what became of one man in one fight, replacing whatever was stamped before.

        A man reaches this twice: knocked out during the fight, then taken prisoner once it is
        decided. Both describe the same casualty, and the second is what became of him - the capture
        is raised off "SkirmishFinished", so it always arrives after the blow that felled him, and
        the last fate written is the one that stuck.
        """
        casualty, _ = self.update_or_create(skirmish=skirmish, warrior=warrior, defaults={"fate": fate})

        return casualty


SkirmishCasualtyManager = SkirmishCasualtyManager.from_queryset(SkirmishCasualtyQuerySet)
