from django.db import models
from django.db.models import Q, Sum, manager


class WarriorQuerySet(models.QuerySet):
    def for_savegame(self, *, savegame_id: int):
        return self.filter(savegame_id=savegame_id)

    def filter_healthy(self):
        return self.filter(condition=self.model.ConditionChoices.CONDITION_HEALTHY)

    def exclude_dead(self):
        return self.exclude(condition=self.model.ConditionChoices.CONDITION_DEAD)

    def filter_faction(self, *, faction_id: int):
        return self.filter(faction=faction_id)

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
        # The refresh matters twice over: it takes the authoritative values, and it is also what turns
        # a generated warrior's float attributes into the integers the arithmetic below assumes
        obj.refresh_from_db()

        grown_fields = ("strength", "dexterity", "max_health", "max_morale", "monthly_salary")
        gains = {field: max(1, round(getattr(obj, field) * self.model.LEVEL_UP_GROWTH)) for field in grown_fields}

        for field, gain in gains.items():
            setattr(obj, field, getattr(obj, field) + gain)

        # Only the five fields touched above: a full save would write back everything else this
        # instance still holds from before
        obj.save(update_fields=grown_fields)

        return gains

    def get_monthly_salary_for_faction(self, *, faction) -> int:
        """
        Calculate the salary of all warriors working for "faction" not being dead.
        """
        return (
            self.exclude(condition=self.model.ConditionChoices.CONDITION_DEAD)
            .filter(faction=faction)
            .aggregate(amount=Sum("monthly_salary"))["amount"]
            or 0
        )

    def set_faction(self, *, obj, faction) -> int:
        """
        Set a new faction for the given warrior.
        """
        obj.refresh_from_db()
        obj.faction = faction
        obj.save(update_fields=("faction",))

        return obj


WarriorManager = WarriorManager.from_queryset(WarriorQuerySet)
