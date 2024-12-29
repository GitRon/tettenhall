from django.db import models
from django.db.models import manager


class MarketplaceQuerySet(models.QuerySet):
    def for_savegame(self, *, savegame_id: int):
        return self.filter(savegame=savegame_id)


class MarketplaceManager(manager.Manager):
    pass


# TODO: this can be put in the class directly, right?
MarketplaceManager = MarketplaceManager.from_queryset(MarketplaceQuerySet)
