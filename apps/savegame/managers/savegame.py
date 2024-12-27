from django.db import models
from django.db.models import manager


class SavegameQuerySet(models.QuerySet):
    def get_for_user(self, *, user_id: int):
        return self.filter(created_by=user_id)

    def get_active(self):
        return self.filter(is_active=True)


class SavegameManager(manager.Manager):
    def set_all_others_from_user_to_inactive(self, *, savegame_id: int, user_id: int):
        """
        Set all other savegames of this savegames user to inactive
        """
        return self.exclude(id=savegame_id, created_by=user_id).update(is_active=False)


SavegameManager = SavegameManager.from_queryset(SavegameQuerySet)
