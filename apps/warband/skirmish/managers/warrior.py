from django.db import models
from django.db.models import Q, manager

from apps.warband.item.models.item import Item


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
        hired has none, and so does a captive whose banner was cleared and a man who walked out of a
        rival's war band - hiring one of those out of the pub would be hiring a man who is not in it.

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
        from apps.warband.skirmish.models.skirmish import Skirmish

        # Said once, against the skirmish rather than against the warrior's two relations to it.
        # Spelling it out as "victorious_faction__isnull=True" on the reverse side would also have
        # matched every warrior who has never fought at all, because the outer join hands those a row
        # of nulls that looks exactly like an undecided fight.
        occupying_skirmishes = Skirmish.objects.filter(Q(month=month) | Q(victorious_faction__isnull=True))

        return self.exclude(quest_contracts__accepted_in_month=month).exclude(
            Q(attacking_skirmishes__in=occupying_skirmishes) | Q(defending_skirmishes__in=occupying_skirmishes)
        )


class WarriorManager(manager.Manager):
    # No warrior's morale ceiling may reach zero. A man at "max_morale = 0" is refilled to zero by
    # "replenish_current_morale", whose "current_morale > 0" guard then never clears his condition, so
    # he stays FLEEING for the rest of the savegame. Every permanent cut goes through this floor.
    MINIMUM_MAX_MORALE = 1

    def reduce_current_health(self, *, obj, damage: int):
        obj.refresh_from_db()

        # Deliberately unfloored, unlike its twin below: how far past zero the blow carried a man is
        # what "handle_reduce_warrior_health" reads to tell a corpse from a captive. The value is
        # normalised the moment that decision is made - see "put_out_of_the_fight" - so nothing
        # outside that one handler ever sees a negative.
        obj.current_health -= damage
        obj.save(update_fields=("current_health",))

        return obj

    def put_out_of_the_fight(self, *, obj, condition: int):
        """
        Settles a warrior who has taken more than he can stand: his condition, and his health at nothing.

        The two belong together. Overkill depth decides which condition he gets, so the health has to
        stay as the blow left it until then - and be tidied away immediately afterwards, because a
        stored -6 reached the card as "-6/8" and cost the monthly healing sweep its whole roll
        carrying him to -5, where "replenish_current_health" still would not wake him.
        """
        obj.current_health = max(obj.current_health, 0)
        obj.condition = condition
        obj.save(update_fields=("current_health", "condition"))

        return obj

    def withdraw_from_the_fight(self, *, obj, lost_max_morale: int):
        """
        Settles a warrior his commander has pulled out: his nerve, his ceiling and his condition.

        The three belong in one write for the reason "put_out_of_the_fight" pairs its two: a warrior
        who is half withdrawn is a warrior some other reader can catch mid-retreat.

        The point of the current morale going to nothing is that it leaves him in exactly the state a
        rout leaves him in. That is what a man walking off the field is, and it is what keeps him
        reachable: the monthly sweep selects on "current_morale__lt=F('max_morale')", so a warrior
        pulled out at full morale and merely charged a point off his ceiling would come back clamped
        to his new maximum, match neither side of that comparison, and never reach the one method that
        clears FLEEING. Nothing anywhere else has to learn that a retreat can be deliberate.

        It is not a second price either. The sweep refills every warrior to his maximum, and nobody
        fights twice in a month, so the only man who can ever see the zero is one his faction failed to
        pay - and an unpaid warrior sits out the sweep today however he left the field.

        The ceiling is what the retreat actually costs, and it is a flat point rather than a share:
        the price of walking away is the same for a levy and for a veteran.
        """
        obj.refresh_from_db()

        obj.current_morale = 0
        obj.max_morale = max(obj.max_morale - lost_max_morale, self.MINIMUM_MAX_MORALE)
        obj.condition = obj.ConditionChoices.CONDITION_FLEEING
        obj.save(update_fields=("current_morale", "max_morale", "condition"))

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

    def increase_max_morale(self, *, obj, gained_max_morale_in_percent: float):
        """
        Raise the ceiling a warrior's morale is measured against.

        Floored at one point the way "apply_level_up_growth" floors its gains: a fifth of a levy's
        five points of morale rounds to nothing, and a gain of zero is not one.

        The current morale is left where it is. A raised ceiling is room to recover into, and the
        monthly sweep is what fills it - topping him up here would hand out this month's morale as
        well as next year's.
        """
        obj.refresh_from_db()
        obj.max_morale += max(1, int(obj.max_morale * gained_max_morale_in_percent))
        obj.save(update_fields=("max_morale",))

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
        as max(1, morale_at_stake) in handle_morale_change_on_resolved_blow.

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

    def set_pub_stock(self, *, obj, is_pub_stock: bool):
        """
        Say whether the next restock may sweep this man off the pub's shelf.
        """
        obj.is_pub_stock = is_pub_stock
        obj.save(update_fields=("is_pub_stock",))

        return obj

    def set_pub_arrival(self, *, obj, month: int | None):
        """
        Say since when this man has been standing in the pub, or that he no longer is.

        A month going in, and None coming back out when somebody hires him: the column is what
        [Warrior.idle_surcharge] prices the wait with, and a veteran back on a roster still carrying
        the date he was last parked would be charged for a wait that ended.
        """
        obj.pub_arrival_month = month
        obj.save(update_fields=("pub_arrival_month",))

        return obj

    def release_from_roster(self, *, obj, faction) -> int:
        """
        Send a warrior away: off the roster and out of the gear the faction paid for.

        The gear stays behind for the reason [strip_equipment] gives - an item belongs to the faction
        and is only wielded by a warrior, so a man who walks off still holding his sword takes it out
        of everyone's reach rather than with him.

        One conditional statement rather than a read, a decision and a save, and the same shape as
        "handle_upgrade_town_building" for the same reason: two overlapping clicks on the one button
        both pass whatever the page checked, and the loser matching no row is what keeps the faction
        from paying severance twice for one man. It also puts the two rules that must never be broken
        in the statement itself - he has to still be on this roster, and he must never be the leader,
        whose loss is what defeats a faction.

        Returns how many rows were released, so a caller can tell the man who went from the click
        that came too late.
        """
        return (
            self.filter(id=obj.id, faction=faction)
            .exclude(id=faction.leader_id)
            .update(faction=None, weapon=None, armor=None)
        )

    def forgive_unpaid_months(self, *, obj):
        """
        Wipe what a warrior is owed, because somebody has settled it another way.

        A man taken onto a roster out of the pub brings the count he left with, and a veteran who
        walked out over unpaid wages left with the full term on him. Carried over, it would put him
        one failed payroll from walking again the month after the faction paid twice his wage to have
        him back - and the warning meanwhile reads "4 of 3 unpaid months", which is a count nothing
        else in the game can produce.

        Not "record_salaries_paid": no wages were paid, a hiring price was.
        """
        obj.refresh_from_db()
        obj.unpaid_months = 0
        obj.save(update_fields=("unpaid_months",))

        return obj

    def set_faction(self, *, obj, faction) -> int:
        """
        Set a new faction for the given warrior.
        """
        obj.refresh_from_db()
        obj.faction = faction
        obj.save(update_fields=("faction",))

        return obj


WarriorManager = WarriorManager.from_queryset(WarriorQuerySet)
