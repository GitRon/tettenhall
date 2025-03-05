import typing

from django.db import models
from django.db.models import manager

if typing.TYPE_CHECKING:
    from apps.savegame.models.savegame import Savegame


class SavegameQuerySet(models.QuerySet):
    def for_user(self, *, user_id: int):
        return self.filter(created_by=user_id)

    def get_active(self):
        return self.filter(is_active=True)


class SavegameManager(manager.Manager):
    def set_all_others_from_user_to_inactive(self, *, savegame_id: int, user_id: int):
        """
        Set all other savegames of this savegames user to inactive
        """
        return self.exclude(id=savegame_id, created_by=user_id).update(is_active=False)

    def get_current_savegame(self, *, user_id: int) -> typing.Optional["Savegame"]:
        """
        Efficient getter for the users current savegame
        """
        try:
            return self.get(created_by=user_id, is_active=True)
        except self.model.DoesNotExist:
            return None

    def activate_savegame(self, *, savegame: "Savegame") -> None:
        """
        Set savegame as active savegame and set all others of the current user as inactive
        """
        self.get_active().for_user(user_id=savegame.created_by_id).update(is_active=False)
        savegame.is_active = True

        savegame.save()


SavegameManager = SavegameManager.from_queryset(SavegameQuerySet)
