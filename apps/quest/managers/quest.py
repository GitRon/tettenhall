from django.db import models
from django.db.models import manager


class QuestQuerySet(models.QuerySet):
    def for_player_faction(self, *, faction_id: int):
        # Only what is pinned to that faction's bulletin board: a quest of the right savegame can
        # still be one that was never offered to the player
        return self.filter(available_town_quests=faction_id)

    def resolvable(self, *, month: int):
        """
        Every quest whose target can still field a defender this month.

        The board is redrawn every month - "handle_offer_quests" deletes it and pins fresh cards - so
        the window this closes is a quest going stale *within* one: it is offered while the target
        still has men, the player then beats them or commits them to another fight, and the card is
        left promising something that can no longer happen. The opposition is that faction's own war
        band now, so accepting it would stage a fight against an empty side, which raises. Asked in
        the queryset rather than checked in the template, because the quest's id comes from the URL
        and hiding a card guards nothing.

        The same question [FactionQuerySet.attackable_targets] asks, and deliberately so - the board
        and the attack path must not disagree about who can be marched on. So a knocked-out faction is
        out even with men still standing at home, and a man already in a fight does not count: every
        warrior fights once a month, and two skirmishes sharing a defender is a savegame that cannot
        be finished.
        """
        # Imported here because the quest model imports this module while being defined itself, and
        # the warrior model reaches back into the quest app through its contracts
        from apps.skirmish.models.warrior import Warrior

        available_defenders = Warrior.objects.filter_healthy().exclude_currently_busy(month=month)

        return self.filter(
            target_faction__is_defeated=False,
            target_faction_id__in=available_defenders.values("faction_id"),
        )


class QuestManager(manager.Manager):
    pass


QuestManager = QuestManager.from_queryset(QuestQuerySet)
