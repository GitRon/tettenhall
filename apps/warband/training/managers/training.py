import typing

from django.db import models
from django.db.models import manager

if typing.TYPE_CHECKING:
    from apps.warband.training.models import Training


class TrainingQuerySet(models.QuerySet):
    def filter_faction(self, *, faction_id: int):
        # The regimen this faction trains by. Parameterised rather than player-scoped: every faction
        # of the savegame owns a row and trains by it, and the caller passing a faction is what says
        # whose month is being worked
        return self.filter(faction_id=faction_id)

    def for_player_faction(self, *, faction_id: int):
        # Every faction of a savegame owns a training row, so scoping to the savegame is not enough
        # to single out the player's own
        return self.filter(faction_id=faction_id)


class TrainingManager(manager.Manager):
    def regimen_for_faction(self, *, faction_id: int) -> Training | None:
        """
        The regimen this faction trains by, or None for a savegame that predates the row.

        A lookup rather than a pick out of a set: the one-to-one to Faction is what guarantees
        there is at most one, so every caller reading a faction's training gets the same answer.
        """
        return self.filter_faction(faction_id=faction_id).first()


TrainingManager = TrainingManager.from_queryset(TrainingQuerySet)
