from django.db import models
from django.db.models import manager


class FactionQuerySet(models.QuerySet):
    def for_savegame(self, *, savegame_id: int):
        return self.filter(savegame=savegame_id)

    def for_player_faction(self, *, faction_id: int):
        return self.filter(id=faction_id)

    def still_in_play(self, *, savegame_id: int):
        """
        Every faction of the savegame still taking part in the game, the player's included.

        The one place deciding who is still in it: a defeated faction gets no month, is never picked
        as a quest target, and cannot be knocked out twice.
        """
        return self.for_savegame(savegame_id=savegame_id).filter(is_defeated=False)

    def rivals_in_play(self, *, player_faction):
        """
        Every faction "player_faction" shares its savegame with that is still on the board.

        The one queryset deciding who the player is up against, whether or not he could march on them
        today: a rival that has been knocked out drops off the rival list for the same reason it stops
        getting a month.
        """
        return self.still_in_play(savegame_id=player_faction.savegame_id).exclude(id=player_faction.id)

    def rivals_still_standing(self, *, player_faction):
        """
        Every rival of "player_faction" that still has somebody on his feet, free or not.

        Wider than [attackable_targets] by exactly the "already in a fight" rule, and that gap is the
        point: it is what lets the faction page tell "they cannot be marched on right now" from "there
        was never anything here to march on". A knocked-out faction and the player's own belong to the
        second, and a sentence explaining the missing button would be a non sequitur on either.
        """
        # Imported here because the faction model imports this module while being defined itself,
        # and the warrior model reaches back into the faction app
        from apps.skirmish.models.warrior import Warrior

        return self.rivals_in_play(player_faction=player_faction).filter(
            id__in=Warrior.objects.filter_healthy().values("faction_id")
        )

    def occupiable_by(self, *, player_faction):
        """
        Every rival of "player_faction" whose town can simply be ridden into.

        The mirror of [rivals_still_standing] rather than the complement of [attackable_by]: a rival
        can be unattackable for having its healthy men already committed to a fight, and a town whose
        defenders are alive, well and merely busy elsewhere is still defended. So this asks the
        positive question - still in play, not the player's own, nobody healthy left to hold it.

        The player's own leader is deliberately not asked about, unlike [attackable_by]. The only way
        a rival reaches this state is that somebody beat his war band, so the leader who did it is on
        "attacking_skirmishes" for the month and "get_available_leader" returns None for every
        occupation that can exist. The march is what paid for the month; this is its follow-up, not a
        second action.

        A leaderless faction is left out. The occupation ends a faction by seizing the man who leads
        it, and there is nothing to seize here - without this the town would be occupiable again every
        month for the rest of the savegame. Unreachable in ordinary play, where a leader who falls
        takes his faction with him, so this is a guard rather than a rule the player will meet.
        """
        # Imported here because the faction model imports this module while being defined itself,
        # and the warrior model reaches back into the faction app
        from apps.skirmish.models.warrior import Warrior

        # The non-null guard is what makes this the negation of [rivals_still_standing] and not an
        # empty queryset. Captives, pub mercenaries and deserters all carry no faction, so without it
        # the subquery yields a NULL, "id NOT IN (..., NULL)" is NULL for every row in SQL, and
        # nothing at all comes back the moment a single prisoner exists. The positive form the sibling
        # method uses is immune to that, which is why only this one needs the filter.
        factions_with_a_healthy_warrior = (
            Warrior.objects.filter_healthy().filter(faction__isnull=False).values("faction_id")
        )

        return (
            self.rivals_in_play(player_faction=player_faction)
            .exclude(id__in=factions_with_a_healthy_warrior)
            .exclude(leader__isnull=True)
        )

    def attackable_targets(self, *, player_faction, month: int):
        """
        Every rival of "player_faction" that is a legitimate target, leaving aside whether the player
        has anyone left to send.

        Split out from [attackable_by] so the faction page can tell "you cannot attack them" from
        "you cannot attack anybody this month" - the message for the second is a non sequitur on the
        player's own faction or on one that is already knocked out.

        "Can be defended" is the same question the defending muster asks, and it has to stay that way:
        a target this offered but whose men the muster then skipped would be a fight created with an
        empty side. So a warrior already committed to a fight does not count towards it either - every
        warrior fights once a month, defenders included, and a man standing in an open skirmish cannot
        also be standing in a new one. Two skirmishes sharing a defender is a savegame that cannot be
        finished: resolving one leaves the other with nobody healthy to post, and the month refuses to
        turn while a skirmish is open.
        """
        # Imported here because the faction model imports this module while being defined itself,
        # and the warrior model reaches back into the faction app
        from apps.skirmish.models.warrior import Warrior

        available_defenders = Warrior.objects.filter_healthy().exclude_currently_busy(month=month)

        # Through a subquery on the warrior rather than a join on the roster, so a faction with
        # several men left standing still comes back once
        return self.rivals_still_standing(player_faction=player_faction).filter(
            id__in=available_defenders.values("faction_id")
        )

    def attackable_by(self, *, player_faction, month: int):
        """
        Every rival "player_faction" may march against this month.

        All of it lives in the queryset rather than in a template condition, because the target's id
        comes from the URL and hiding a button guards nothing. The leader is checked here too even
        though he stands on the attacking side: an attack he cannot march on is no attack at all,
        and a rule kept somewhere else is how the button and the view drift apart.

        How often the player may attack is not asked here either, and deliberately so. Every warrior
        fights once a month, the leader joins every attack, so a war band that has marched is a
        leader who is busy - and this returns nothing for the rest of the month, whoever the target
        is. A separate per-rival cap sat here once; it never got to decide anything and only looked
        like a rule.
        """
        if player_faction is None or player_faction.get_available_leader(month=month) is None:
            return self.none()

        return self.attackable_targets(player_faction=player_faction, month=month)


class FactionManager(manager.Manager):
    def add_captive(self, *, faction, warrior):
        faction.captured_warriors.add(warrior)

    def remove_captive(self, *, faction, warrior):
        faction.captured_warriors.remove(warrior)

    def remove_mercenary_from_pub(self, *, faction, warrior):
        """
        Take a hired mercenary off the pub's shelf.

        Not cosmetic. "handle_restock_pub_mercenaries" clears the stock with
        "available_mercenaries.all().delete()", which is a warrior queryset and deletes the rows
        themselves - so a man left linked to the pub is deleted at the start of the next month, after
        he has been paid for, equipped and marched. This is what keeps him out of that queryset.
        """
        faction.available_mercenaries.remove(warrior)

    def replenish_fyrd_reserve(self, *, faction, new_recruits: int):
        faction.refresh_from_db()

        # Update reserve
        faction.fyrd_reserve += new_recruits
        faction.save()

        return faction

    def reduce_fyrd_reserve(self, *, faction, drafted_warriors: int):
        faction.refresh_from_db()

        # Update reserve
        faction.fyrd_reserve = max(0, faction.fyrd_reserve - drafted_warriors)
        faction.save()

        return faction


FactionManager = FactionManager.from_queryset(FactionQuerySet)
