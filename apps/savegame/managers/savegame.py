import random
import typing

from django.db import models
from django.db.models import manager

from apps.faction.models import Culture, Faction
from apps.marketplace.models import Marketplace
from apps.training.models import Training

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

    def create_record(
        self, *, town_name: str, faction_name: str, faction_culture_id: int, created_by_id: int
    ) -> "Savegame":
        """
        Create a new savegame and other required objects
        """

        # Create savegame object
        marketplace = Marketplace.objects.create(town_name=town_name)
        savegame = self.model.objects.create(
            name=f"{town_name}/{faction_name}",
            marketplace=marketplace,
            created_by_id=created_by_id,
        )

        # Create player faction
        player_faction = Faction.objects.create(
            name=faction_name,
            culture_id=faction_culture_id,
            savegame=savegame,
            fyrd_reserve=random.randint(2, 5),
        )
        savegame.player_faction = player_faction

        # Create training object
        Training.objects.create(category=random.choice(Training.TrainingCategory.choices)[0], faction=player_faction)

        # TODO: create faction generator
        [
            Faction.objects.create(
                name=f"Faction {i+1}",
                culture=random.choice(Culture.objects.all()),
                savegame=savegame,
            )
            for i in range(random.randint(3, 5))
        ]

        # Set savegame as active savegame and set all others of the current user as inactive
        self.activate_savegame(savegame=savegame)

        return savegame

    def activate_savegame(self, *, savegame: "Savegame") -> None:
        """
        Set savegame as active savegame and set all others of the current user as inactive
        """
        self.get_active().for_user(user_id=savegame.created_by_id).update(is_active=False)
        savegame.is_active = True

        savegame.save()


SavegameManager = SavegameManager.from_queryset(SavegameQuerySet)
