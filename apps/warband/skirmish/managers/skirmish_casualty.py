from django.db import models
from django.db.models import manager


class SkirmishCasualtyQuerySet(models.QuerySet):
    def for_skirmish(self, *, skirmish_id: int):
        return self.filter(skirmish_id=skirmish_id)

    def killed_of_faction(self, *, faction_id: int):
        """
        The men of one faction who were killed in a fight.

        Read off the dead man's own faction, which nothing clears once he is dead. A man captured
        earlier and killed fighting for the side that took him is that side's dead, not his old one's.
        """
        return self.filter(fate=self.model.FateChoices.FATE_KILLED, warrior__faction_id=faction_id)


class SkirmishCasualtyManager(manager.Manager):
    def create_record(self, *, skirmish, warrior, fate: int, killed_by=None, fell_as_a_leader: bool = False):
        """
        Stamps what became of one man in one fight, replacing whatever was stamped before.

        A man reaches this twice: knocked out during the fight, then taken prisoner once it is
        decided. Both describe the same casualty, and the second is what became of him - the capture
        is raised off "SkirmishFinished", so it always arrives after the blow that felled him, and
        the last fate written is the one that stuck. The killer and the leader flag are written with
        the fate, so they always describe the fate the row ends on.
        """
        casualty, _ = self.update_or_create(
            skirmish=skirmish,
            warrior=warrior,
            defaults={"fate": fate, "killed_by": killed_by, "fell_as_a_leader": fell_as_a_leader},
        )

        return casualty


SkirmishCasualtyManager = SkirmishCasualtyManager.from_queryset(SkirmishCasualtyQuerySet)
