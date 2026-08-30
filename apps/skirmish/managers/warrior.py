from django.db import models
from django.db.models import Q, manager

from apps.item.models.item import Item


class WarriorQuerySet(models.QuerySet):
    def for_savegame(self, *, savegame_id: int):
        return self.filter(savegame_id=savegame_id)

    def filter_healthy(self):
        return self.filter(condition=self.model.ConditionChoices.CONDITION_HEALTHY)

    def exclude_dead(self):
        return self.exclude(condition=self.model.ConditionChoices.CONDITION_DEAD)

    def filter_faction(self, *, faction_id: int):
        return self.filter(faction=faction_id)

    def for_player_faction(self, *, faction_id: int):
        # The warriors the player commands. Narrower than "for_savegame", which also holds every
        # rival's men, the captives and the mercenaries still standing in a pub
        return self.filter(faction_id=faction_id)

    def in_pub_of(self, *, faction_id: int):
        """
        The mercenaries standing in this faction's pub, waiting to be hired.

        Membership of "available_mercenaries" rather than a missing faction: a mercenary nobody has
        hired has none, and so does a deserter and a captive whose banner was cleared - hiring one of
        those out of the pub would be hiring a man who is not in it.

        Parameterised by faction on purpose. Every faction owns a pub set already, and the caller
        passing the player's is what says "the player hires from his own town" - not this method.
        """
        return self.filter(available_pub_mercenaries=faction_id)

    def exclude_currently_busy(self, *, month: int):
        """
        Every warrior fights once a month, and never two fights at the same time.

        Three ways to be busy. Signed on to a quest this month, which is the only one this used to
        know about. Already committed to a fight this month. And still standing on the roster of a
        fight nobody has played out - that last one because an unresolved skirmish carries over into
        the next month, where the month check on its own would hand the same warrior out again while
        he is still in it.

        The quest half is one "NOT EXISTS" about the warrior. Spelled as a filter over the joined
        contracts it read per through-row instead: a warrior holding contracts in month 1 and month 3
        came back as free in month 3, because the month-1 row satisfied "this row is not month 3".

        Both sides of a skirmish are asked, attacking and defending alike: a captive who changed
        banners has fought all the same, and a warrior is no less busy for having been the one
        marched against.
        """
        # Imported here because the skirmish model reaches back into this module through the warrior
        # model it points at
        from apps.skirmish.models.skirmish import Skirmish

        # Said once, against the skirmish rather than against the warrior's two relations to it.
        # Spelling it out as "victorious_faction__isnull=True" on the reverse side would also have
        # matched every warrior who has never fought at all, because the outer join hands those a row
        # of nulls that looks exactly like an undecided fight.
        occupying_skirmishes = Skirmish.objects.filter(Q(month=month) | Q(victorious_faction__isnull=True))

        return self.exclude(quest_contracts__accepted_in_month=month).exclude(
            Q(attacking_skirmishes__in=occupying_skirmishes) | Q(defending_skirmishes__in=occupying_skirmishes)
        )


class WarriorManager(manager.Manager):
    def reduce_current_health(self, *, obj, damage: int):
        obj.refresh_from_db()
        obj.current_health -= damage
        obj.save(update_fields=("current_health",))

        return obj

    def replenish_current_health(self, *, obj, healed_points: int):
        obj.refresh_from_db()
        obj.current_health += healed_points

        if obj.current_health > obj.max_health:
            obj.current_health = obj.max_health

        if obj.current_health > 0:
            obj.condition = obj.ConditionChoices.CONDITION_HEALTHY

        obj.save(update_fields=("current_health", "condition"))

        return obj

    def set_condition(self, *, obj, condition: int):
        obj.condition = condition
        obj.save(update_fields=("condition",))

        return obj

    def take_item_away(self, *, item):
        """
        Ensure that the given "item" is not being actively used by any warrior
        """
        self.filter(weapon=item).update(weapon=None)
        self.filter(armor=item).update(armor=None)

    def replenish_current_morale(self, *, obj, recovered_morale_points: int):
        """
        Give the morale back, and with it the nerve to fight again.

        A rout is the one condition morale owns, so this owns the way out of it the same way
        "replenish_current_health" owns the way out of unconsciousness. Without the condition, a
        warrior who fled without a scratch ended the month at full morale and still "FLEEING": the
        healing sweep only looks at the wounded, so the one method that could have cleared him never
        ran on him, and he drew salary for the rest of the game without ever fighting again.

        Only the fleeing rally. An unconscious man's way back is the health path - and he reaches
        this method every month, because the morale sweep excludes only the dead - while a dead one
        has no way back at all, so a bare "his morale is up, so he is healthy" would wake the first
        and resurrect the second.

        Rallied to zero is not rallied, which is why the morale is asked about as well as the
        condition.
        """
        obj.refresh_from_db()
        obj.current_morale += recovered_morale_points

        if obj.current_morale > obj.max_morale:
            obj.current_morale = obj.max_morale

        if obj.current_morale > 0 and obj.is_fleeing:
            obj.condition = obj.ConditionChoices.CONDITION_HEALTHY

        obj.save(update_fields=("current_morale", "condition"))

        return obj

    def reduce_morale(self, *, obj, lost_morale: int):
        """
        Drop morale to a minimum of zero
        """
        obj.refresh_from_db()
        obj.current_morale = 0 if obj.current_morale - lost_morale < 0 else obj.current_morale - lost_morale
        obj.save(update_fields=("current_morale",))

        return obj

    def reduce_max_morale(self, *, obj, lost_max_morale_in_percent: float):
        """
        Drop max morale to a minimum of zero
        """
        obj.refresh_from_db()
        lost_morale = int(obj.max_morale * lost_max_morale_in_percent)
        obj.max_morale = 0 if obj.max_morale - lost_morale < 0 else obj.max_morale - lost_morale
        obj.current_morale = min(obj.current_morale, obj.max_morale)
        obj.save(update_fields=("max_morale", "current_morale"))

        return obj

    def increase_morale(self, *, obj, increased_morale: int):
        """
        Increase morale to a defined maximum
        """
        obj.refresh_from_db()
        if obj.current_morale + increased_morale > obj.max_morale:
            obj.current_morale = obj.max_morale
        else:
            obj.current_morale = obj.current_morale + increased_morale
        obj.save(update_fields=("current_morale",))

        return obj

    def increase_experience(self, *, obj, experience: int):
        """
        Increase experience
        """
        obj.refresh_from_db()
        obj.experience += experience
        obj.save(update_fields=("experience",))

        return obj

    def apply_level_up_growth(self, *, obj) -> dict[str, int]:
        """
        Grow everything a level touches by LEVEL_UP_GROWTH, and return what each one gained.

        Only the maxima, never the current values. Unlike training, experience arrives *during* a
        skirmish - handle_experience_gain_on_warrior_incapacitation fires the moment somebody drops -
        so raising current_health here would top a warrior up mid-battle and make winning harder the
        cheapest way to survive. The warrior reads as wounded against his new ceiling instead, which
        is what handle_progress_warrior_training already does with max_morale.

        Every gain is floored at one point. A tenth of a small attribute rounds to nothing: round(v *
        0.1) is 0 for every v from 1 to 5, five included, because Python rounds halves to even. The
        fyrd generator sits at STATS_MU = 5 and MORALE_MU = 5, so a levy would otherwise level up,
        gain a single hit point off his health, and charge more for it. Same reasoning and same shape
        as max(1, morale_at_stake) in handle_morale_change_on_warrior_defends_all_damage.

        The *_progress columns are deliberately not involved. They belong to training, which fills and
        resets them, so keeping a fractional remainder there would mean a level-up eats a month of
        training and a month of training triggers level-up growth. Levels round per event.
        """
        # Refreshed so the arithmetic below runs on the authoritative values rather than on whatever
        # this instance was still holding
        obj.refresh_from_db()

        grown_fields = ("strength", "dexterity", "max_health", "max_morale", "monthly_salary")
        gains = {field: max(1, round(getattr(obj, field) * self.model.LEVEL_UP_GROWTH)) for field in grown_fields}

        for field, gain in gains.items():
            setattr(obj, field, getattr(obj, field) + gain)

        # Only the five fields touched above: a full save would write back everything else this
        # instance still holds from before
        obj.save(update_fields=grown_fields)

        return gains

    def get_payroll_for_faction(self, *, faction) -> list:
        """
        Everybody "faction" owes wages to this month, cheapest man first.

        The dead draw nothing, and a captive is off the roster already because capture clears his
        faction. Handed over warrior by warrior rather than as a sum, because a faction that cannot
        pay the whole bill has to know who it did manage to pay - and the cost card has to know who
        it would fail to pay. [Payroll] is what both of them ask; there used to be an aggregate
        beside this for the card, and the two could answer differently.

        The order is the rule: paying from the cheapest up fits the most men into whatever silver
        there is, and leaves the shortfall sitting on the dearest. Those are the veterans, the ones
        whose salary grew with every level, so insolvency costs a faction its best men first.
        """
        return list(
            self.exclude(condition=self.model.ConditionChoices.CONDITION_DEAD)
            .filter(faction=faction)
            # By id as well, or two warriors on the same salary come back in whatever order the
            # database feels like and the tests below them flap
            .order_by("monthly_salary", "id")
        )

    def record_salaries_paid(self, *, warrior_list: list) -> list:
        """
        Note that these warriors got their wages, which forgives however many months they went
        without.

        Taken a roster at a time rather than a warrior at a time, because the salary run always has
        the whole list in hand and a per-warrior write would put two queries per man on the month
        advance. No "refresh_from_db" either, for the same reason the batching is safe: these
        instances came out of "get_payroll_for_faction" moments earlier in the same transaction, and
        nothing in a month touches "unpaid_months" but this method and its unpaid twin. Mutating them
        before the write is what keeps the objects handed to the events correct without reading them
        back.
        """
        for warrior in warrior_list:
            warrior.unpaid_months = 0

        self.bulk_update(warrior_list, ("unpaid_months",))

        return warrior_list

    def record_salaries_unpaid(self, *, warrior_list: list) -> list:
        """
        Note another month these warriors went without their wages.
        """
        for warrior in warrior_list:
            warrior.unpaid_months += 1

        self.bulk_update(warrior_list, ("unpaid_months",))

        return warrior_list

    def strip_equipment(self, *, obj):
        """
        Take back whatever the warrior is carrying, without touching who owns it.

        An item belongs to the faction ("Item.owner") and is only ever wielded by a warrior, so a
        man who leaves the roster still holding his gear takes it out of reach rather than with him:
        "Faction.get_all_unoccupied_items" skips anything a warrior is wearing, so the faction could
        neither re-equip nor sell it ever again.
        """
        obj.refresh_from_db()
        obj.weapon = None
        obj.armor = None
        obj.save(update_fields=("weapon", "armor"))

        return obj

    def transfer_equipment_ownership(self, *, obj, new_owner) -> list:
        """
        Hand whatever the warrior is carrying to his new faction, and leave it on him.

        Ownership and use are two different things: an item belongs to a faction ("Item.owner") and is
        wielded by a warrior. A man hired out of the pub arrives carrying gear nobody owns, and unowned
        gear is invisible to "Faction.get_all_unoccupied_items" - so it could never be re-equipped onto
        anybody else or sold, while "get_weapon_or_fallback" builds its fallbacks with
        "owner=self.faction". Either the items come with him or they are taken off him; leaving them
        ownerless is the one outcome that strands them.

        Deliberately not "Item.objects.update_ownership", which nulls the bearer's weapon and armor as
        it hands the item over. That is right for a purchase, where nobody is wearing it yet, and it
        would disarm the man the faction has just paid for.
        """
        equipment = [item for item in (obj.weapon, obj.armor) if item is not None]

        for item in equipment:
            item.owner = new_owner

        Item.objects.bulk_update(equipment, ("owner",))

        return equipment

    def set_faction(self, *, obj, faction) -> int:
        """
        Set a new faction for the given warrior.
        """
        obj.refresh_from_db()
        obj.faction = faction
        obj.save(update_fields=("faction",))

        return obj


WarriorManager = WarriorManager.from_queryset(WarriorQuerySet)
