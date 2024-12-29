from django.db import models
from django.db.models import Sum, manager


class WarriorQuerySet(models.QuerySet):
    def filter_healthy(self):
        return self.filter(condition=self.model.ConditionChoices.CONDITION_HEALTHY)


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

        obj.save(update_fields=("current_health",))

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
        obj.refresh_from_db()
        obj.current_morale += recovered_morale_points

        if obj.current_morale > obj.max_morale:
            obj.current_morale = obj.max_morale

        obj.save(update_fields=("current_morale",))

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

    def get_weekly_salary_for_faction(self, *, faction) -> int:
        """
        Calculate the salary of all warriors working for "faction" not being dead.
        """
        return (
            self.exclude(condition=self.model.ConditionChoices.CONDITION_DEAD)
            .filter(faction=faction)
            .aggregate(amount=Sum("weekly_salary"))["amount"]
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
