from django.db import models
from django.db.models import manager


class QuestQuerySet(models.QuerySet):
    def for_player_faction(self, *, faction_id: int):
        # Only what is pinned to that faction's bulletin board: a quest of the right savegame can
        # still be one that was never offered to the player
        return self.filter(available_town_quests=faction_id)

    def resolvable(self):
        """
        Every quest whose target can still field a defender.

        A quest outlives the month it was offered in, so the faction it names may have been flattened
        since - and accepting one then stages a fight against an empty side, which raises. Asked in
        the queryset rather than checked in the template, because the quest's id comes from the URL
        and hiding a card guards nothing.
        """
        # Imported here because the quest model imports this module while being defined itself, and
        # the warrior model reaches back into the quest app through its contracts
        from apps.skirmish.models.warrior import Warrior

        return self.filter(target_faction__warriors__condition=Warrior.ConditionChoices.CONDITION_HEALTHY).distinct()


class QuestManager(manager.Manager):
    pass


QuestManager = QuestManager.from_queryset(QuestQuerySet)
